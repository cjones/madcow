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

"""Get song lyrics from lyricwiki"""

from urlparse import urljoin
import logging as log
import re

from include.utils import Module, stripHTML
from include.useragent import getsoup
from include.google import Google, NonRedirectResponse

__version__ = '2.0'
__author__ = 'cj_ <cjones@gruntle.org>'

class Main(Module):

    pattern = re.compile(r'^\s*sing\s+(.+?)\s*$', re.I)
    help = 'sing <song/artist>'

    baseurl = u'http://lyricwiki.org/'
    searchurl = urljoin(baseurl, u'/Special:Search')
    advert = ' - Lyrics from LyricWiki'

    _br = r'\s*<br\s*/?\s*>\s*'
    _line_break = re.compile(_br, re.I)
    _verse_break = re.compile(_br * 2, re.I)

    def __init__(self, *args, **kwargs):
        self.google = Google()
        super(Main, self).__init__()

    def normalize(self, lyrics):
        verses = self._verse_break.split(lyrics)
        verses = [self._line_break.sub(' / ', verse) for verse in verses]
        verses = [stripHTML(verse) for verse in verses]
        return '\n'.join(verses).strip()

    def response(self, nick, args, kwargs):
        try:
            try:
                url = self.google.lucky(args[0] + u' site:lyricwiki.org')
            except NonRedirectResponse:
                opts = {'search': args[0], 'ns0': 1}
                soup = getsoup(self.searchurl, referer=self.baseurl, opts=opts)
                url = urljoin(self.baseurl, soup.li.a['href'])
            soup = getsoup(url, referer=self.baseurl)
            title = self.render(soup.title).replace(self.advert, '')
            lyrics = self.render(soup.find('div', 'lyricbox'))
            lyrics = self.normalize(lyrics)
            if not lyrics or lyrics == 'None':
                raise ValueError('no results')
            return u'%s:\n%s' % (title, lyrics)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, "Couldn't find them, they must suck")

    def render(self, node):
        return node.renderContents().decode('utf-8', 'ignore')


if __name__ == '__main__':
    from include.utils import test_module
    import sys
    sys.argv.append('sing around the world daft punk')
    test_module(Main)
