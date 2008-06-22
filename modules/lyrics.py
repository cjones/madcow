#!/usr/bin/env python

"""Get song lyrics from lyricwiki"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from include.utils import stripHTML
from include.BeautifulSoup import BeautifulSoup
from urlparse import urljoin

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Chris Jones'
__all__ = []

class Main(Module):
    pattern = re.compile(r'^\s*sing\s+(.+?)\s*$', re.I)
    help = 'sing <song/artist>'
    error = 'no results'
    baseurl = 'http://lyricwiki.org/'
    searchurl = urljoin(baseurl, '/Special:Search')

    def response(self, nick, args, kwargs):
        try:
            opts = {'search': args[0], 'ns0': 1}
            page = geturl(self.searchurl, referer=self.baseurl, opts=opts)
            soup = BeautifulSoup(page)
            url = str(soup.findAll('li')[0].find('a')['href'])
            url = urljoin(self.baseurl, url)
            page = geturl(url, referer=self.baseurl)
            soup = BeautifulSoup(page)
            lyrics = str(soup.find('div', attrs={'class': 'lyricbox'}))
            lyrics = lyrics.replace('<br />', '\n')
            lyrics = stripHTML(lyrics)
            if not lyrics or lyrics == 'None':
                raise Exception, 'no results'
            return lyrics
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
