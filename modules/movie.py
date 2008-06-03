#!/usr/bin/env python

"""Module stub"""

from include.utils import Module, Base
import logging as log
import re
from include.useragent import geturl   # mimic browser
from urlparse import urljoin
from include.utils import stripHTML    # strip HTML/unescape entities

__version__ = '0.1'
__author__ = 'cj_ <cjones@gmail.com>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Christopher Jones'
__all__ = []

# global regex
reopts = re.I + re.DOTALL
whitespace = re.compile(r'\s+')
html_title = re.compile(r'<title>(.*?)</title>', re.I)
year = re.compile(r'\(\d{4}\)\s*$')

class IMDB(Base):
    baseurl = 'http://www.imdb.com/'
    search = urljoin(baseurl, '/find')
    search_title = 'IMDb  Search'
    movies = re.compile('<a\s+.*?href=(["\'])(/title/tt\d+/)\\1.*?>(.*?</a>)',
            reopts)
    rating = re.compile(r'<b>User Rating:</b>.*<b>([0-9.]+)/10</b>', reopts)

    def rate(self, movie):
        try:
            page = geturl(self.search, opts={'s': 'all', 'q': movie})
            title = html_title.search(page).group(1)
            if title == self.search_title:
                # normalize search results
                movies = self.movies.findall(page)
                movies = [(y, z) for x, y, z in movies]
                movies = [(path, normalize(title)) for path, title in movies]
                movies = [(path, title) for path, title in movies if title]

                # see if we can find an exact match
                url = None
                for path, title in movies:
                    if title == movie:
                        url = urljoin(self.baseurl, path)
                        break

                # no exact match, take first option returned
                if not url:
                    url = urljoin(self.baseurl, movies[0][0])

                # load actual page & title
                page = geturl(url, referer=self.search)
                title = html_title.search(page).group(1)

            # get rating and generate response
            rating = self.rating.search(page).group(1)
            response = 'IMDB'
            if normalize(title) != movie:
                response += ' [%s]' % stripHTML(title)
            response += ': %s' % rating
            return response

        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return 'IMDB: ?'


class RottenTomatoes(Base):
    baseurl = 'http://www.rottentomatoes.com/'
    search = urljoin(baseurl, '/search/search.php')
    movies = re.compile('<a class=movie-link href="(.*?)"', reopts)
    _rating = re.compile(r'<a onmouseover="toggle_display\(\'bubble_allCritics\'\)" onmouseout="toggle_display\(\'bubble_allCritics\'\)" title="(.*?%)"', reopts)

    def rate(self, movie):
        try:
            opts={'sitesearch': 'rt', 'search': movie}
            page = geturl(self.search, opts=opts, referer=self.baseurl)
            print page
            title = html_title.search(page).group(1)
            print title

            #titleurl = self.titles.findall(html)[0]
            #titleurl = urljoin(self.baseurl, titleurl)
            #html = geturl(titleurl, referer=self.searchurl)
            #rating = self._rating.search(html).group(1)
            #return rating
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return 'Freshness: ?'


class MovieRatings(Base):
    imdb = IMDB()
    rt = RottenTomatoes()

    def rate(self, movie):
        movie = normalize(movie)
        #ratings = [self.imdb.rate(movie), self.rt.rate(movie)]
        ratings = [self.imdb.rate(movie)]
        ratings = [rating for rating in ratings if rating is not None]
        return ', '.join(ratings)


def normalize(name):
    name = stripHTML(name)
    name = year.sub('', name)
    name = name.lower()
    name = name.strip()
    name = whitespace.sub(' ', name)
    return name

class Main(Module):
    pattern = re.compile(r'^\s*rate\s+(.+?)\s*$', re.I)
    error = 'does that movie even exist?'
    movie = MovieRatings()

    def response(self, nick, args, **kwargs):
        try:
            return '%s: %s' % (nick, self.movie.rate(args[0]))
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
