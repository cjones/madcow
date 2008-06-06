#!/usr/bin/env python

"""Look up song lyrics"""

from include.utils import Module, Base
import logging as log
import re
from include.useragent import geturl
from include.utils import stripHTML
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
import random

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Christopher Jones'
__all__ = []

whitespace = re.compile(r'\s+')
badchars = re.compile(r'[^a-z0-9 ]', re.I)

class LyricsFreak(Base):
    baseurl = 'http://www.lyricsfreak.com/'
    search = urljoin(baseurl, '/search.php')
    search_opts = {'sa.x': '0', 'sa.y': '0', 'sa': 'Search'}
    result = re.compile(r'<td class="lyric">.*?<a href="(.*?)" title="(.*?)">',
            re.I + re.DOTALL)

    _newline = re.compile(r'[\r\n]+')
    _leadbreak = re.compile(r'^(?:<br(?:\s+/)?\s*>\s*)+', re.I + re.DOTALL)
    _endbreak = re.compile(r'(?:<br(?:\s+/)?\s*>\s*)+$', re.I + re.DOTALL)
    _break = re.compile(r'<br(?:\s+/)?\s*>', re.I + re.DOTALL)
    _spam = '!! &nbsp; &nbsp;Download to your phone.'

    def get_song_for_artist(self, qsong, qartist):
        opts = dict(self.search_opts)
        opts['type'] = 'artist'
        opts['q'] = qartist
        page = geturl(self.search, opts=opts, referer=self.baseurl)
        results = self.result.findall(page)
        exact = None
        for url, artist in results:
            if normalize(artist) == normalize(qartist):
                exact = url
                break
        if not exact:
            exact = results[0][0]
        url = urljoin(self.baseurl, exact)
        url = urljoin(url, 'lyrics.html')
        page = geturl(url, referer=self.search)
        results = self.result.findall(page)
        exact = None
        for url, song in results:
            song = song.replace(' lyrics', '')
            if normalize(song) == normalize(qsong):
                exact = url
                break
        if not exact:
            exact = results[0][0]
        url = urljoin(self.baseurl, exact)
        return self.get_lyrics_from_url(url)

    def get_lyrics_from_url(self, url):
        page = geturl(url, referer=self.baseurl)
        soup = BeautifulSoup(page)
        content = soup.find('div', attrs={'id': 'content'})
        [div.extract() for div in content.findAll('div')]
        [link.extract() for link in content.findAll('a')]
        [script.extract() for script in content.findAll('script')]
        lines = [str(line) for line in content.contents]
        data = ''.join(lines)
        data = self._newline.sub('', data)
        data = self._leadbreak.sub('', data)
        data = self._endbreak.sub('', data)
        lines = self._break.split(data)
        verses = []
        while True:
            try:
                i = lines.index('')
                verse, lines = lines[:i], lines[i+1:]
                verses.append(verse)
            except ValueError:
                verses.append(lines)
                break
        for i, verse in enumerate(verses):
            verse = ' / '.join(verse)
            verse = whitespace.sub(' ', verse)
            verses[i] = verse
        if self._spam in verses:
            del verses[verses.index(self._spam)]
        return verses

    def search_for_song(self, song):
        return ['not implemented yet, supply an artist']

    def random_song_for_artist(self, song):
        return ['not implemented yet, supply a song name + artist']


class Main(Module):
    r = r'^\s*sing\s+(?:song\s+(.+?)(?:\s+by\s+(.+?))?|(.+?))(?:\s+(full))?\s*$'
    pattern = re.compile(r, re.I)
    help = 'sing [song <song> [by <artist>]|<artist>] [full]'
    error = "couldn't find that song :("

    def __init__(self, madcow=None):
        self.freak = LyricsFreak()

    def response(self, nick, args, **kwargs):
        try:
            song, artist, random_song, full = args
            if song:
                if artist:
                    response = self.freak.get_song_for_artist(song, artist)
                else:
                    response = self.freak.search_for_song(song)
            elif random_song:
                response = self.freak.random_song_for_artist(random_song)
            else:
                response = 'what?'
            if response:
                if full:
                    return '\n'.join(response)
                else:
                    return random.choice(response)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


def normalize(name):
    name = stripHTML(name)
    name = badchars.sub('', name)
    name = name.lower()
    name = name.strip()
    name = whitespace.sub(' ', name)
    return name

if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
