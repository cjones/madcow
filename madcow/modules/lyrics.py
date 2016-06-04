"""Get song lyrics from lyricwiki"""

from urlparse import urlparse, urljoin, urlunparse
from urllib import urlencode
from cgi import parse_qsl
import re
from madcow.util import Module, strip_html
from madcow.util.google import Google, NonRedirectResponse
from madcow.util.text import *


class Main(Module):

    pattern = re.compile(r'^\s*sing\s+(.+?)\s*$', re.I)
    help = 'sing <song/artist/lyric>'
    error = "Couldn't find them, they must suck"

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        kwargs['req'].quoted = True
        url = urlunparse(('https', 'www.google.com', 'search', '',
            urlencode({'num': '100', 'safe': 'off', 'hl': 'en', 'q': 'site:songmeanings.com ' + args[0]}), ''))
        soup = self.getsoup(url)
        new = None
        for h3 in soup.findAll('h3', attrs={'class': 'r'}):
            uri = urlparse(h3.a['href'])
            if uri.path == '/url':
                url = dict(parse_qsl(uri.query))['q']
                uri = urlparse(url)
                if re.search('/songs/view/\d+', uri.path) is not None:
                    new = urlunparse(uri._replace(query='', fragment=''))
                    break
                elif re.search('/profiles/(submissions|interaction)/\d+/comments', uri.path) is not None:
                    soup = self.getsoup(url)
                    for a in soup.find('a', title='Direct link to comment'):
                        new = urlunparse(urlparse(a.parent['href'])._replace(fragment='', query=''))
                        break
                if new:
                    break
        if new:
            url = new
            try:
                soup = self.getsoup(url)
                try:
                    title = re.sub('\s+Lyrics\s+\|\s+SongMeanings.*$', '', soup.title.renderContents())
                except StandardError:
                    title = 'Unknown artist/song, check parsing code!'
                text = soup.find('div', attrs={'class': re.compile(r'.*lyric-box.*')})
                for a in text('a'):
                    a.extract()
            except StandardError:
                self.log.warn('unable to find textblock from url {0!r} (query: {1!r})'.format(url, args[0]))
                return u'{nick}: {error}'.format(error=self.error, **kwargs)

            try:
                lyrics = decode(text.renderContents(), 'utf-8')
                return u'\n'.join(['[{}]'.format(title)] + filter(None,
                    [line.strip() for line in strip_html(lyrics).splitlines()]))
            except StandardError:
                self.log.exception('error parsing lyrics for query: {0!r}'.format(args[0]))
                return u'{nick}: {error}'.format(error=self.error, **kwargs)
