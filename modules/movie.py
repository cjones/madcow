#!/usr/bin/env python

"""Get rating for a movie"""

import sys
import re
import os
from include.utils import Base
from include.useragent import UserAgent
from urlparse import urljoin

reopts = re.I + re.DOTALL
ua = UserAgent()

class IMDB(Base):
    baseurl = 'http://www.imdb.com/'
    searchurl = urljoin(baseurl, '/find')
    titles = re.compile('<a\s+.*?href=(["\'])(/title/tt\d+/)\\1.*?>', reopts)
    title = re.compile(r'<title>(.*?)</title>', reopts)
    _rating = re.compile(r'<b>User Rating:</b>.*<b>([0-9.]+)/10</b>', reopts)

    def rating(self, movie):
        html = ua.openurl(self.searchurl, referer=self.baseurl,
                opts={'s': 'tt', 'q': movie})
        title = self.title.search(html).group(1)
        if 'Search' in title:
            titleurl = [item[1] for item in self.titles.findall(html)][0]
            titleurl = urljoin(self.baseurl, titleurl)
            html = ua.openurl(titleurl, referer=self.searchurl)
        try:
            rating = self._rating.search(html).group(1)
        except:
            rating = '?'
        return rating

class RottenTomatoes(Base):
    baseurl = 'http://www.rottentomatoes.com/'
    searchurl = urljoin(baseurl, '/search/search.php')
    titles = re.compile('<a class=movie-link href="(.*?)"', reopts)
    #XXX might be a better way to get this..
    _rating = re.compile(r'<a onmouseover="toggle_display\(\'bubble_allCritics\'\)" onmouseout="toggle_display\(\'bubble_allCritics\'\)" title="(.*?%)"', reopts)

    def freshness(self, movie):
        html = ua.openurl(self.searchurl, referer=self.baseurl,
                opts={'sitesearch': 'rt', 'search': movie})
        titleurl = self.titles.findall(html)[0]
        titleurl = urljoin(self.baseurl, titleurl)
        html = ua.openurl(titleurl, referer=self.searchurl)
        rating = self._rating.search(html).group(1)
        return rating

class Main(Base):
    pattern = re.compile(r'^\s*rate\s+(.+?)\s*$', re.I)
    enabled = True
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
            return '%s: problem with query: %s' % (nick, e)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
