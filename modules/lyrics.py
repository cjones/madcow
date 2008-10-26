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

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from include.utils import stripHTML
from include.BeautifulSoup import BeautifulSoup
from urlparse import urljoin
from include.google import Google, NonRedirectResponse

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*sing\s+(.+?)\s*$', re.I)
    help = 'sing <song/artist>'
    error = 'no results'
    baseurl = 'http://lyricwiki.org/'
    searchurl = urljoin(baseurl, '/Special:Search')
    advert = ' - lyrics from LyricWiki'
    google = Google()
    _br = r'\s*<br\s*/?\s*>\s*'
    _line_break = re.compile(_br, re.I)
    _verse_break = re.compile(_br * 2, re.I)

    def normalize(self, lyrics):
        verses = self._verse_break.split(lyrics)
        verses = [self._line_break.sub(' / ', verse) for verse in verses]
        verses = [stripHTML(verse) for verse in verses]
        return '\n'.join(verses)

    def response(self, nick, args, kwargs):
        try:
            try:
                url = self.google.lucky(args[0] + ' site:lyricwiki.org')
            except NonRedirectResponse:
                opts = {'search': args[0], 'ns0': 1}
                page = geturl(self.searchurl, referer=self.baseurl, opts=opts)
                soup = BeautifulSoup(page)
                url = str(soup.findAll('li')[0].find('a')['href'])
                url = urljoin(self.baseurl, url)
            page = geturl(url, referer=self.baseurl)
            soup = BeautifulSoup(page)
            title = stripHTML(str(soup.find('title'))).replace(self.advert, '')
            lyrics = str(soup.find('div', attrs={'class': 'lyricbox'}))
            lyrics = self.normalize(lyrics)
            if not lyrics or lyrics == 'None':
                raise Exception, 'no results'
            return title + ':\n' + lyrics
        except Exception, error:
            log.warn('error in %s: %s' % (self.__module__, error))
            log.exception(error)
            return '%s: %s' % (nick, error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
