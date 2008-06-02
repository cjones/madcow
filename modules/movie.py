#!/usr/bin/env python

"""Get rating for a movie"""

import re
from include.utils import Base, Module
from include.useragent import geturl
from urlparse import urljoin
import logging as log

reopts = re.I + re.DOTALL

class IMDB(Base):
    baseurl = 'http://www.imdb.com/'
    searchurl = urljoin(baseurl, '/find')
    titles = re.compile('<a\s+.*?href=(["\'])(/title/tt\d+/)\\1.*?>', reopts)
    title = re.compile(r'<title>(.*?)</title>', reopts)
    _rating = re.compile(r'<b>User Rating:</b>.*<b>([0-9.]+)/10</b>', reopts)

    def rating(self, movie):
        try:
            html = geturl(self.searchurl, referer=self.baseurl,
                    opts={'s': 'tt', 'q': movie})
            title = self.title.search(html).group(1)
            titleurl = [item[1] for item in self.titles.findall(html)][0]
            titleurl = urljoin(self.baseurl, titleurl)
            html = geturl(titleurl, referer=self.searchurl)
            rating = self._rating.search(html).group(1)
            return rating
        except:
            return '?'


class RottenTomatoes(Base):
    baseurl = 'http://www.rottentomatoes.com/'
    searchurl = urljoin(baseurl, '/search/search.php')
    titles = re.compile('<a class=movie-link href="(.*?)"', reopts)
    _rating = re.compile(r'<a onmouseover="toggle_display\(\'bubble_allCritics\'\)" onmouseout="toggle_display\(\'bubble_allCritics\'\)" title="(.*?%)"', reopts)

    def freshness(self, movie):
        try:
            html = geturl(self.searchurl, referer=self.baseurl,
                    opts={'sitesearch': 'rt', 'search': movie})
            titleurl = self.titles.findall(html)[0]
            titleurl = urljoin(self.baseurl, titleurl)
            html = geturl(titleurl, referer=self.searchurl)
            rating = self._rating.search(html).group(1)
            return rating
        except:
            return '?'


class Main(Module):
    pattern = re.compile(r'^\s*rate\s+(.+?)\s*$', re.I)
    require_addressing = True
    help = 'rate <movie> - get ratings for a movie'
    format = '%s: freshness: %s, imdb rating: %s'

    def __init__(self, madcow=None):
        self.imdb = IMDB()
        self.rt = RottenTomatoes()

    def response(self, nick, args, **kwargs):
        try:
            movie = args[0]
            return self.format % (nick, self.rt.freshness(movie),
                    self.imdb.rating(movie))
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: problem looking that movie up' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
