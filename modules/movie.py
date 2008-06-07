#!/usr/bin/env python

"""Module stub"""

from include.utils import Module, Base
import logging as log
import re
from include.useragent import geturl
from urlparse import urljoin
from include.utils import stripHTML

__version__ = '0.2'
__author__ = 'cj_ <cjones@gmail.com>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Christopher Jones'
__all__ = ['IMDB', 'RottenTomatoes', 'MovieRatings']

# global
reopts = re.I + re.DOTALL
whitespace = re.compile(r'\s+')
html_title = re.compile(r'<title>(.*?)</title>', re.I)
year = re.compile(r'\(\d{4}\)\s*$')
badchars = re.compile(r'[^a-z0-9 ]', re.I)

class IMDB(Base):
    """Interface to IMDB"""
    baseurl = 'http://imdb.com/'
    search = urljoin(baseurl, '/find')
    search_title = 'IMDb  Search'
    movies = re.compile('<a\s+.*?href=(["\'])(/title/tt\d+/)\\1.*?>(.*?</a>)',
            reopts)
    rating = re.compile(r'<b>User Rating:</b>.*<b>([0-9.]+)/10</b>', reopts)

    def rate(self, movie):
        """Get the rating for a movie"""
        try:
            page = geturl(self.search, opts={'s': 'all', 'q': movie})
            movie = normalize(movie)
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

        except:
            return


class RottenTomatoes(Base):
    """Interface to Rotten Tomatoes"""
    baseurl = 'http://www.rottentomatoes.com/'
    search = urljoin(baseurl, '/search/search.php')
    search_title = 'ROTTEN TOMATOES: Movie Reviews &amp; Previews'
    movies = re.compile(r'<a class=movie-link href="(.*?)">(.*?)</a>', reopts)
    movie_title = re.compile(r'<h1 class="movie_title">(.*?)</h1>', reopts)
    rating = re.compile(r'<div id="bubble_allCritics".*?>\s*(\d+%)', reopts)

    def rate(self, movie):
        """Get the freshness rating of a movie"""
        try:
            opts={'sitesearch': 'rt', 'search': movie}
            page = geturl(self.search, opts=opts, referer=self.baseurl)
            movie = normalize(movie)
            title = html_title.search(page).group(1)
            if title == self.search_title:
                # normalize search results
                movies = self.movies.findall(page)
                movies = [(path, normalize(title)) for path, title in movies]

                # look for exact match
                url = None
                for path, title in movies:
                    if title == movie:
                        url = urljoin(self.baseurl, path)
                        break

                # no exact match, take first one
                if not url:
                    url = urljoin(self.baseurl, movies[0][0])

                # load page
                page = geturl(url, referer=self.search)

            # find rating
            title = self.movie_title.search(page).group(1)
            rating = self.rating.search(page).group(1)

            # construct response
            response = 'Freshness'
            if normalize(title) != movie:
                response += ' [%s]' % stripHTML(title)
            response += ': %s' % rating
            return response

        except:
            return


class MovieRatings(Base):
    """Class that gets movie ratings from IMDB and Rotten Tomatoes"""
    imdb = IMDB()
    rt = RottenTomatoes()

    def rate(self, movie):
        """Get movie ratings from imdb and rotten tomatoes"""
        ratings = [self.imdb.rate(movie), self.rt.rate(movie)]
        ratings = [rating for rating in ratings if rating is not None]
        if ratings:
            return ', '.join(ratings)
        return 'movie not found'


class Main(Module):
    """Autoloaded by MadCow"""
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


def normalize(name):
    """Normalize a movie title for easy comparison"""
    name = stripHTML(name)
    name = year.sub('', name)
    name = badchars.sub(' ', name)
    name = name.lower()
    name = name.strip()
    name = whitespace.sub(' ', name)
    return name

if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
