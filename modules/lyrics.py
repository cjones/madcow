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

__version__ = u'0.2'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*sing\s+(.+?)\s*$', re.I)
    help = u'sing <song/artist>'
    error = u'no results'
    baseurl = u'http://lyricwiki.org/'
    searchurl = urljoin(baseurl, u'/Special:Search')
    advert = u' - lyrics from LyricWiki'
    google = Google()
    _br = r'\s*<br\s*/?\s*>\s*'
    _line_break = re.compile(_br, re.I)
    _verse_break = re.compile(_br * 2, re.I)

    def normalize(self, lyrics):
        verses = self._verse_break.split(lyrics)
        verses = [self._line_break.sub(u' / ', verse) for verse in verses]
        verses = [stripHTML(verse) for verse in verses]
        return u'\n'.join(verses).strip()

    def response(self, nick, args, kwargs):
        try:
            try:
                url = self.google.lucky(args[0] + u' site:lyricwiki.org')
            except NonRedirectResponse:
                opts = {u'search': args[0], u'ns0': 1}
                page = geturl(self.searchurl, referer=self.baseurl, opts=opts)
                soup = BeautifulSoup(page)
                url = unicode(soup.findAll(u'li')[0].find(u'a')[u'href'])
                url = urljoin(self.baseurl, url)
            page = geturl(url, referer=self.baseurl)
            soup = BeautifulSoup(page)
            title = soup.find(u'title').string.replace(self.advert, u'')
            lyrics = unicode(soup.find(u'div', attrs={u'class': u'lyricbox'}))
            lyrics = self.normalize(lyrics)
            if not lyrics or lyrics == u'None':
                raise Exception, u'no results'
            return u'%s:\n%s' % (title, lyrics)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
