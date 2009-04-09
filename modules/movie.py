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

"""Rate movies"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from urlparse import urljoin
from include.utils import stripHTML

reopts = re.I | re.DOTALL
whitespace = re.compile(r'\s+')
html_title = re.compile(r'<title>(.*?)</title>', re.I)
year = re.compile(r'\(\d{4}\)\s*$')
badchars = re.compile(r'[^a-z0-9 ]', re.I)
_reversed_article = re.compile(r'^(.*?),\s*(the|an?)\s*$', re.I)
_articles = re.compile(r'^\s*(the|an?)\s+', re.I)

class IMDB(object):

    """Interface to IMDB"""

    baseurl = u'http://imdb.com/'
    search = urljoin(baseurl, u'/find')
    search_title = u'IMDb Search'
    movies = re.compile(u'<a\s+.*?href=(["\'])(/title/tt\d+/)\\1.*?>(.*?</a>)',
                        reopts)
    rating = re.compile(r'<div class="meta">.*?<b>([0-9.]+)/10</b>', reopts)

    def rate(self, movie):
        """Get the rating for a movie"""
        try:
            page = geturl(self.search, opts={u's': u'all', u'q': movie})
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
            response = u'IMDB'
            if normalize(title) != movie:
                response += u' [%s]' % stripHTML(title)
            response += u': %s/10' % rating
            return response

        except:
            raise


class RottenTomatoes(object):

    """Interface to Rotten Tomatoes"""

    baseurl = u'http://www.rottentomatoes.com/'
    search = urljoin(baseurl, u'/search/search.php')
    search_title = u'ROTTEN TOMATOES: Movie Reviews &amp; Previews'
    movies = re.compile(r'<a href="(/m/.*?/)">(.*?)</a>', reopts)
    movie_title = re.compile(r'<h1 class="movie_title clearfix">(.*?)</h1>',
                             reopts)
    rating = re.compile(u'<div id="tomatometer_score".*?>.*?>([0-9.]+)', reopts)

    def rate(self, movie):
        """Get the freshness rating of a movie"""
        try:
            opts={u'sitesearch': u'rt', u'search': movie}
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
            response = u'Freshness'
            if normalize(title) != movie:
                response += u' [%s]' % stripHTML(title)
            response += u': %s%%' % rating
            return response

        except Exception, error:
            log.exception(error)


class MetaCritic(object):

    baseurl = u'http://www.metacritic.com/'
    search = urljoin(baseurl, u'/search/process')
    movie_opts = {u'sort': u'relevance',
                  u'termType': u'all',
                  u'ts': None,
                  u'ty': u'1',
                  u'x': u'24',
                  u'y': u'10',
                  }
    result = re.compile(r'<strong>(?:Film|Video):</strong>\s+<a href="([^"]+)'
                        r'"><b>(.*?)</b>', reopts)
    critic_rating = re.compile(r'ALT="Metascore: ([0-9.]+)"')
    user_rating = re.compile(r'<span class="subhead">([0-9.]+)</span>')

    def rate(self, movie):
        try:
            opts = dict(self.movie_opts)
            opts[u'ts'] = movie
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
                critic_rating = u'Critics: ' + critic_rating + u'/100'
            except:
                critic_rating = None
            try:
                user_rating = self.user_rating.search(page).group(1)
                user_rating = u'Users: ' + user_rating + u'/10'
            except:
                user_rating = None

            title = html_title.search(page).group(1)
            title = title.replace(u': Reviews', u'')

            response = u'Meta'
            if normalize(title) != movie:
                response += u' [%s]' % stripHTML(title)
            ratings = [i for i in (critic_rating, user_rating) if i is not None]
            ratings = u', '.join(ratings)
            if ratings:
                response += u' - %s' % ratings
            return response
        except:
            pass


class MovieRatings(object):

    """Class that gets movie ratings from IMDB and Rotten Tomatoes"""

    sources = (IMDB(), RottenTomatoes(), MetaCritic())
    baseurl = u'http://videoeta.com/'
    topurl = urljoin(baseurl, u'/theaters.html')
    movieurl = urljoin(baseurl, u'/movie/')
    movies = re.compile(r'/movie/(.*?).>(.*?)<', re.DOTALL)

    def topmovies(self):
        doc = geturl(self.topurl)
        results = self.movies.findall(doc)[:10]
        results = [u'%2s: %s - %s%s' % (i+1, r[1], self.movieurl, r[0])
                   for i, r in enumerate(results)]
        results.insert(0, u'>>> Top Movies At Box Office <<<')
        return u'\n'.join(results)

    def rate(self, movie):
        """Get movie ratings from imdb and rotten tomatoes"""
        ratings = [source.rate(movie) for source in self.sources]
        ratings = [rating for rating in ratings if rating is not None]
        if ratings:
            return u', '.join(ratings)
        return u'movie not found'


class Main(Module):

    """Autoloaded by MadCow"""

    pattern = re.compile(r'^\s*(?:(rate)\s+(.+?)|(topmovies))\s*$', re.I)
    error = u'does that movie even exist?'
    movie = MovieRatings()
    help = u'[rate <movie>|topmovies] - get info about movies'

    def response(self, nick, args, kwargs):
        try:
            if args[0] == u'rate':
                response = u'%s: %s' % (nick, self.movie.rate(args[1]))
            elif args[2] == u'topmovies':
                response = self.movie.topmovies()
            return unicode(response)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, self.error)


def normalize(name):
    """Normalize a movie title for easy comparison"""
    name = stripHTML(name)
    name = year.sub(u'', name)
    name = _reversed_article.sub(r'\2 \1', name)
    name = _articles.sub(u'', name)
    name = badchars.sub(u' ', name)
    name = name.lower()
    name = name.strip()
    name = whitespace.sub(u' ', name)
    return name


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
