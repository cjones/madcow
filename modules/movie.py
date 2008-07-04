#!/usr/bin/env python

"""Module stub"""

from include.utils import Module
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

class IMDB:
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
            response += ': %s/10' % rating
            return response

        except:
            return


class RottenTomatoes:
    """Interface to Rotten Tomatoes"""
    baseurl = 'http://www.rottentomatoes.com/'
    search = urljoin(baseurl, '/search/search.php')
    search_title = 'ROTTEN TOMATOES: Movie Reviews &amp; Previews'
    movies = re.compile(r'<a href="(/m/.*?/)">(.*?)</a>', reopts)
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

        except Exception, msg:
            log.exception(msg)
            return


class MetaCritic:
    baseurl = 'http://www.metacritic.com/'
    search = urljoin(baseurl, '/search/process')
    movie_opts = {
        'sort': 'relevance',
        'termType': 'all',
        'ts': None,
        'ty': '1',
        'x': '24',
        'y': '10',
    }
    result = re.compile(r'<strong>(?:Film|Video):</strong>\s+<a href="([^"]+)"><b>(.*?)</b>', re.I+re.DOTALL)
    critic_rating = re.compile(r'ALT="Metascore: ([0-9.]+)"')
    user_rating = re.compile(r'<span class="subhead">([0-9.]+)</span>')

    def rate(self, movie):
        try:
            opts = dict(self.movie_opts)
            opts['ts'] = movie
            page = geturl(self.search, opts=opts)
            movie = normalize(movie)
            movies = self.result.findall(page)
            movies = [(path, normalize(title)) for path, title in movies]
            url = None
            for path, title in movies:
                if title == movie:
                    url = urljoin(self.baseurl, path)
                    break
            if not url:
                url = urljoin(self.baseurl, movies[0][0])
            page = geturl(url, referer=self.search)
            try:
                critic_rating = self.critic_rating.search(page).group(1)
                critic_rating = 'Critics: ' + critic_rating + '/100'
            except:
                critic_rating = None
            try:
                user_rating = self.user_rating.search(page).group(1)
                user_rating = 'Users: ' + user_rating + '/10'
            except:
                user_rating = None

            title = html_title.search(page).group(1)
            title = title.replace(': Reviews', '')

            response = 'Meta'
            if normalize(title) != movie:
                response += ' [%s]' % stripHTML(title)
            ratings = [i for i in (critic_rating, user_rating) if i is not None]
            ratings = ', '.join(ratings)
            if ratings:
                response += ' - %s' % ratings
            return response
        except:
            return


class MovieRatings:
    """Class that gets movie ratings from IMDB and Rotten Tomatoes"""
    sources = (
        IMDB(),
        RottenTomatoes(),
        MetaCritic(),
    )
    baseurl = 'http://videoeta.com/'
    topurl = urljoin(baseurl, '/theaters.html')
    movieurl = urljoin(baseurl, '/movie/')
    movies = re.compile(r'/movie/(.*?).>(.*?)<', re.DOTALL)

    def topmovies(self):
        doc = geturl(self.topurl)
        results = self.movies.findall(doc)[:10]
        results = ['%2s: %s - %s%s' % (i+1, r[1], self.movieurl, r[0])
                   for i, r in enumerate(results)]
        results.insert(0, '>>> Top Movies At Box Office <<<')
        return '\n'.join(results)

    def rate(self, movie):
        """Get movie ratings from imdb and rotten tomatoes"""
        ratings = [source.rate(movie) for source in self.sources]
        ratings = [rating for rating in ratings if rating is not None]
        if ratings:
            return ', '.join(ratings)
        return 'movie not found'


class Main(Module):
    """Autoloaded by MadCow"""
    pattern = re.compile(r'^\s*(?:(rate)\s+(.+?)|(topmovies))\s*$', re.I)
    error = 'does that movie even exist?'
    movie = MovieRatings()
    help = '[rate <movie>|topmovies] - get info about movies'

    def response(self, nick, args, kwargs):
        try:
            if args[0] == 'rate':
                response = '%s: %s' % (nick, self.movie.rate(args[1]))
            elif args[2] == 'topmovies':
                response = self.movie.topmovies()
            return response
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


_reversed_article = re.compile(r'^(.*?),\s*(the|an?)\s*$', re.I)
def normalize(name):
    """Normalize a movie title for easy comparison"""
    name = stripHTML(name)
    name = year.sub('', name)
    name = _reversed_article.sub(r'\2 \1', name)
    name = badchars.sub(' ', name)
    name = name.lower()
    name = name.strip()
    name = whitespace.sub(' ', name)
    return name

if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
