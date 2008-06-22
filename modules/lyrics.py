#!/usr/bin/env python

"""Get song lyrics from lyricwiki"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from include.utils import stripHTML
from include.BeautifulSoup import BeautifulSoup
from urlparse import urljoin
from include.google import Google

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
    advert = ' - lyrics from LyricWiki'
    google = Google()

    def response(self, nick, args, kwargs):
        try:
            url = self.google.lucky(args[0] + ' site:lyricwiki.org')
            page = geturl(url, referer=self.baseurl)
            soup = BeautifulSoup(page)
            title = stripHTML(str(soup.find('title'))).replace(self.advert, '')
            lyrics = str(soup.find('div', attrs={'class': 'lyricbox'}))
            lyrics = lyrics.replace('<br />', '\n')
            lyrics = stripHTML(lyrics)
            if not lyrics or lyrics == 'None':
                raise Exception, 'no results'
            return title + ':\n' + lyrics
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
