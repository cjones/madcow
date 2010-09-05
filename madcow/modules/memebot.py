#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

raise ImportError('this needs to be rewritten to not use fucking sql, jesus')

"""Watch URLs in channel, punish people for living under a rock"""

import re
import os
import urlparse
import datetime
import random
from madcow.util import Module

from cgi import parse_qsl
from urllib import urlencode

# XXX hack to work around busted pysqlite/sqlobject integration
try:
    from pysqlite2 import _sqlite
    if _sqlite.sqlite_version.count('.') == 3:
        i = _sqlite.sqlite_version.rindex('.')
        _sqlite.sqlite_version = _sqlite.sqlite_version[:i]
except ImportError:
    pass

from sqlobject import *

# sqlobject explodes on reloads
try:
    class URL(SQLObject):

        class sqlmeta:

            table = 'url'

        url = StringCol()
        clean = StringCol()
        author = ForeignKey('Author')
        channel = ForeignKey('Channel')
        citations = IntCol(default=0)
        posted = DateTimeCol(default = datetime.datetime.now)
        comments = MultipleJoin('Comments')

        @property
        def truncated_url(self):
            if len(self.url) > 48:
                return self.url[:48] + ' ... ' + self.url[-4:]
            else:
                return self.url


    class Author(SQLObject):

        name = StringCol(alternateID=True, length=50)
        urls = MultipleJoin('URL')
        comments = MultipleJoin('Comments')
        points_new = IntCol(default=0)
        points_old = IntCol(default=0)
        points_credit = IntCol(default=0)


    class Channel(SQLObject):

        name = StringCol(alternateID=True, length=50)
        urls = MultipleJoin('URL')


    class Comments(SQLObject):

        text = StringCol()
        author = ForeignKey('Author')
        url = ForeignKey('URL')

except:
    pass


class MemeBot(Module):

    pattern = Module._any
    allow_threading = False
    priority = 10
    terminate = False
    require_addressing = False
    help = 'score [name | x - y] - get memescore'
    match_url_re = re.compile(r'(http://\S+)', re.I)
    score_request_re = re.compile(
            r'^\s*score(?:(?:\s+|[:-]+\s*)(\S+?)(?:\s*-\s*(\S+))?)?\s*$', re.I)
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
             'are you serious?']

    def __init__(self, madcow):
        self.encoding = madcow.config.main.charset
        config = madcow.config.memebot
        engine = config.db_engine
        uri = engine + '://'
        if engine == 'sqlite':
            uri += os.path.join(madcow.base,
                                'data/db-%s-memes' % madcow.namespace)
        else:
            user = config.db_user
            if config.db_pass:
                user += ':' + config.db_pass
            host = config.db_host
            if not host:
                host = 'localhost'
            if config.db_port:
                host += ':' + config.db_port
            uri += '%s@%s/%s' % (user, host, config.db_name)
        try:
            sqlhub.processConnection = connectionForURI(uri)
        except Exception, error:
            self.log.warn('invalid uri: %s (%s)' % (uri, error))
            self.enabled = False
            return

        # show raw SQL being dispatched if loglevel is debug
        if self.log.root.level <= self.log.DEBUG:
            URL._connection.debug = True
            Author._connection.debug = True
            Channel._connection.debug = True
            Comments._connection.debug = True

        URL.createTable(ifNotExists=True)
        Author.createTable(ifNotExists=True)
        Channel.createTable(ifNotExists=True)
        Comments.createTable(ifNotExists=True)

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
        #print 'became: %r' % url
        return url

    def get_score_for_author(self, author):
        return ((author.points_new    *  1) +
                (author.points_old    * -2) +
                (author.points_credit *  2))

    def get_scores(self):
        scores = [(author.name, self.get_score_for_author(author))
                   for author in Author.select()]
        return sorted(scores, key=lambda item: item[1], reverse=True)

    def response(self, nick, args, kwargs):
        nick = nick.lower()
        addressed = kwargs['addressed']
        message = args[0].encode(self.encoding, 'replace')

        if addressed:
            try:
                x, y = self.score_request_re.search(message).groups()
                return self.score_response(x, y)
            except AttributeError:
                pass

        try:
            orig = self.match_url_re.search(message).group(1)
        except AttributeError:
            return

        clean = self.clean_url(orig)

        comment1, comment2 = re.split(re.escape(orig), message)
        try:
            comment1 = self.colon_header_re.search(comment1).group(1)
        except AttributeError:
            pass

        comment1 = comment1.strip()
        comment2 = comment2.strip()

        try:
            me = Author.byName(nick)
        except SQLObjectNotFound:
            me = Author(name=nick)

        try:
            try:
                old = URL.select(URL.q.clean == clean)[0]
            except:
                raise SQLObjectNotFound

            if comment1:
                Comments(url=old, text=comment1, author=me)
            if comment2:
                Comments(url=old, text=comment2, author=me)

            # chew them out unless its my own
            if old.author.name.lower() != nick:
                old.author.points_credit = old.author.points_credit + 1
                me.points_old = me.points_old + 1
                old.citations = old.citations + 1

                return '%s First posted by %s on %s' % (
                        random.choice(self.riffs),
                        old.author.name,
                        old.posted)

        except SQLObjectNotFound:
            channel = kwargs['channel'].lower()
            try:
                channel = Channel.byName(channel)
            except SQLObjectNotFound:
                channel = Channel(name=channel)

            url = URL(url=orig, clean=clean, author=me, channel=channel)

            if comment1:
                Comments(url=url, text=comment1, author=me)
            if comment2:
                Comments(url=url, text=comment2, author=me)
            me.points_new = me.points_new + 1

        except Exception, error:
            self.log.warn('error in module %s' % self.__module__)
            self.log.exception(error)

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


Main = MemeBot

