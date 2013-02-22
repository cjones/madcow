"""Get song lyrics from lyricwiki"""

from urlparse import urljoin
import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.google import Google, NonRedirectResponse
from madcow.util.text import *

def ipython():
    import sys
    # only call first time to protect from looping (shell traps SIGINT, very annoying and hard to escape)
    if not ipython.__dict__.get('x'):
        ipython.x = 1
        a, sys.argv[:] = sys.argv[:], ['ipython']
        try:
            from IPython.Shell import IPShellEmbed as S
            f = sys._getframe(1)
            S()('\nlocals: ' + ', '.join(sorted(f.f_locals)) if f.f_locals else '', f.f_locals, f.f_globals)
        finally:
            sys.argv[:] = a


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
            try:
                title = strip_html(soup.find('a', 'pw_title').renderContents()).strip()
            except StandardError:
                title = 'Unknown artist/song, check parsing code!'
            text = soup.find('div', id='textblock')
        except StandardError:
            self.log.warn('unable to find textblock from url {0!r} (query: {1!r})'.format(url, args[0]))
            return u'{nick}: {error}'.format(error=self.error, **kwargs)

        try:
            lyrics = decode(text.renderContents(), 'utf-8')
            return u'\n'.join(['[{}]'.format(title)] + filter(None, [line.strip() for line in strip_html(lyrics).splitlines()]))
        except StandardError:
            self.log.exception('error parsing lyrics for query: {0!r}'.format(args[0]))
            return u'{nick}: {error}'.format(error=self.error, **kwargs)
