"""Get song lyrics from lyricwiki"""

from urlparse import urljoin
import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.google import Google, NonRedirectResponse

class Main(Module):

    pattern = re.compile(r'^\s*sing\s+(.+?)\s*$', re.I)
    help = 'sing <song/artist>'
    baseurl = u'http://lyrics.wikia.com/'
    searchurl = urljoin(baseurl, u'/Special:Search')
    _br = r'\s*<br\s*/?\s*>\s*'
    _line_break = re.compile(_br, re.I)
    _verse_break = re.compile(_br * 2, re.I)
    error = "Couldn't find them, they must suck"

    def init(self):
        self.google = Google()

    def normalize(self, lyrics):
        verses = self._verse_break.split(lyrics)
        verses = [self._line_break.sub(' / ', verse) for verse in verses]
        verses = [strip_html(verse) for verse in verses]
        return '\n'.join(verses).strip()

    def response(self, nick, args, kwargs):
        try:
            url = self.google.lucky(u'site:lyrics.wikia.com ' + args[0])
        except NonRedirectResponse:
            opts = {'search': args[0], 'ns0': 1}
            soup = getsoup(self.searchurl, referer=self.baseurl, opts=opts)
            url = urljoin(self.baseurl, soup.li.a['href'])
        soup = getsoup(url, referer=self.baseurl)
        title = self.render(soup.title).split(' - LyricWiki')[0]
        title = title.replace(':', ' - ')
        title = title.replace('_', ' ')
        lyrics = soup.find('div', 'lyricbox')
        for spam in lyrics('div', 'rtMatcher'):
            spam.extract()
        lyrics = self.render(lyrics)
        lyrics = self.normalize(lyrics)
        if not lyrics or lyrics == 'None':
            raise ValueError('no results')
        return u'%s:\n%s' % (title, lyrics)

    def render(self, node):
        return node.renderContents().decode('utf-8', 'ignore')
