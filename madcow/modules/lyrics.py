"""Get song lyrics from lyricwiki"""

from urlparse import urljoin
import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.google import Google, NonRedirectResponse
from madcow.util.text import *

class Main(Module):

    pattern = re.compile(r'^\s*sing\s+(.+?)\s*$', re.I)
    help = 'sing <song/artist/lyric>'
    error = "Couldn't find them, they must suck"

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        try:
            url = self.google.lucky(u'site:songmeanings.net ' + args[0])
        except NonRedirectResponse:
            self.log.warn('no url for query {0!r} found from google lucky'.format(args[0]))
            return u'{nick}: {error}'.format(error=self.error, **kwargs)

        try:
            soup = getsoup(url)
            text = soup.find('div', id='textblock')
        except StandardError:
            self.log.warn('unable to find textblock from url {0!r} (query: {1!r})'.format(url, args[0]))
            return u'{nick}: {error}'.format(error=self.error, **kwargs)

        try:
            lyrics = decode(text.renderContents(), 'utf-8')
            return u'\n'.join(filter(None, [line.strip() for line in strip_html(lyrics).splitlines()]))
        except StandardError:
            self.log.exception('error parsing lyrics for query: {0!r}'.format(args[0]))
            return u'{nick}: {error}'.format(error=self.error, **kwargs)
