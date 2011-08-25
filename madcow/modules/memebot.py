"""Watch URLs in channel, punish people for living under a rock"""

import re
import os
import urlparse
from datetime import datetime
import random
import shelve
from cgi import parse_qsl
from urllib import urlencode
from madcow.util import Module
import threading
from Queue import Queue

SaveDB = object()

class Main(Module):

    pattern = Module._any
    allow_threading = False
    priority = 10
    terminate = False
    require_addressing = False
    help = 'score [name | x - y] - get memescore'
    match_url_re = re.compile(r'(https?://\S+)', re.I)
    score_request_re = re.compile(r'^\s*score(?:(?:\s+|[:-]+\s*)(\S+?)(?:\s*-\s*(\S+))?)?\s*$', re.I)
    colon_header_re = re.compile(r'^\s*(.*?)\s*:\s*$')
    get_frag_re = re.compile(r'^(.*)#([^;/?:@=&]*)$')
    riffs = ['OLD MEME ALERT!',
             'omg, SO OLD!',
             'Welcome to yesterday.',
             'been there, done that.',
             'you missed the mememobile.',
             'oldest. meme. EVAR.',
             'jesus christ you suck.',
             'you need a new memesource, bucko.',
             'that was funny the first time i saw it.',
             'new to the internet?',
             'i think that came installed with the internet.',
             'are you serious?',
             'CHOO!! CHOO!! ALL ABOARD THE OLD MEME TRAIN!',
             ]

    def init(self):
        self.db = shelve.open(os.path.join(self.madcow.base, 'db', 'memebot'), writeback=True)
        self.db.setdefault('urls', {})
        self.db.setdefault('nicks', {})

        # save changes to db without blocking
        self.queue = Queue()
        self.lock = threading.RLock()
        thread = threading.Thread(target=self.updater)
        thread.setDaemon(True)
        thread.start()

    def updater(self):
        while True:
            signal = self.queue.get()
            if signal is None:
                break
            if signal is SaveDB:
                with self.lock:
                    self.db.sync()

    def clean_url(self, url):
        # stolen from urlparse.urlsplit(), which doesn't handle
        # splitting frags correctly
        netloc = query = fragment = ''
        i = url.find(':')
        scheme = url[:i].lower()
        url = url[i+1:]
        if url[:2] == '//':
            delim = len(url)
            for c in '/?#':
                wdelim = url.find(c, 2)
                if wdelim >= 0:
                    delim = min(delim, wdelim)
            netloc, url = url[2:delim], url[delim:]
        if '#' in url:
            try:
                url, fragment = self.get_frag_re.search(url).groups()
            except:
                pass
        if '?' in url:
            url, query = url.split('?', 1)

        ### now for memebots normalizing..
        # make hostname lowercase and remove www
        netloc = netloc.lower()
        netloc = urlparse.unquote(netloc).replace('+', ' ')
        if netloc.startswith('www.') and len(netloc) > 4:
            netloc = netloc[4:]
        if netloc.endswith('.') and len(netloc) > 1:
            netloc = netloc[:-1]
        # all urls have trailing slash
        if url == '':
            url = '/'
        url = urlparse.unquote(url).replace('+', ' ')
        # remove empty query settings, these are usually form artifacts
        # and put them in order
        try:
            query = urlencode([
                item for item in sorted(parse_qsl(query)) if item[1]])
        except Exception, e:
            query = ''
        # ignore fragments
        fragment = ''

        args = [scheme, netloc, url, query, fragment]
        url = urlparse.urlunsplit(args)
        return url

    def get_score_for_nick(self, nick):
        author = self.get_author(nick)
        return author['new'] * 1 + author['old'] * -2 + author['credit'] * 2

    def get_scores(self):
        scores = [(nick, self.get_score_for_nick(nick)) for nick, author in self.db['nicks'].iteritems()]
        return sorted(scores, key=lambda item: item[1], reverse=True)

    def get_author(self, nick):
        return self.db['nicks'].setdefault(nick, {'old': 0, 'new': 0, 'credit': 0})

    def response(self, nick, args, kwargs):
        nick = nick.lower()
        message = args[0]
        if kwargs['addressed']:
            try:
                return self.score_response(*self.score_request_re.search(message).groups())
            except AttributeError:
                pass
        try:
            orig = self.match_url_re.search(message).group(1)
        except AttributeError:
            return
        clean = self.clean_url(orig)
        try:
            url = self.db['urls'][clean]
        except KeyError:
            url = None
        if url is None:
            self.db['urls'][clean] = {
                    'orig': orig,
                    'date': datetime.now(),
                    'count': 1,
                    'channel': kwargs['channel'].lower(),
                    'nick': nick}
            self.get_author(nick)['new'] += 1
            self.queue.put(SaveDB)
        elif url['nick'] != nick:
            url['count'] += 1
            self.get_author(nick)['old'] += 1
            self.get_author(url['nick'])['credit'] += 1
            self.queue.put(SaveDB)
            return u'%s First posted by %s on %s' % (random.choice(self.riffs), url['nick'], url['date'].ctime())

    def score_response(self, x, y):
        scores = self.get_scores()
        size = len(scores)
        if x is None:
            scores = scores[:10]
            x = 1
        elif x.isdigit():
            x = int(x)
            if x == 0:
                x = 1
            if x > size:
                x = size
            if y and y.isdigit():
                y = int(y)
                if y > size:
                    y = size
                scores = scores[x-1:y]
            else:
                scores = [scores[x-1]]
        else:
            for i, data in enumerate(scores):
                name, score = data
                if name.lower() == x.lower():
                    scores = [scores[i]]
                    x = i+1
                    break
        out = []
        for i, data in enumerate(scores):
            name, score = data
            out.append('#%s: %s (%s)' % (i + x, name, score))
        return ', '.join(out)

    def __del__(self):
        self.db.close()
        self.queue.put(None)
