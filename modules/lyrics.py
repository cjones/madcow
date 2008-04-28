#!/usr/bin/env python

"""Get lyrics from http://www.lyricsfreak.com/"""

import sys
import re
import os
from include.utils import Base, UserAgent, stripHTML
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
import random

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
_namespace = 'madcow'
_dir = '..'

class Lyrics(Base):
    _baseurl = 'http://www.lyricsfreak.com/'
    _search = urljoin(_baseurl, '/search.php')
    _artist_songs = urljoin(_baseurl, '/SECTION/ARTIST/lyrics.html')
    _opts = {'type': 'title', 'sa.x': 21, 'sa.y': 20, 'sa': 'Search', 'q': ''}
    _re_by = re.compile(r'\s*by\s*')
    _re_dash = re.compile(r'\s*-\s*')
    _links = {'title': re.compile(r'lyrics')}
    _newline = re.compile(r'[\r\n]+')
    _break = re.compile(r'<br(?:\s+/)?\s*>', re.I + re.DOTALL)
    _leadbreak = re.compile(r'^(?:<br(?:\s+/)?\s*>\s*)+', re.I + re.DOTALL)
    _endbreak = re.compile(r'(?:<br(?:\s+/)?\s*>\s*)+$', re.I + re.DOTALL)
    _whitespace = re.compile(r'\s+')

    def __init__(self):
        self.ua = UserAgent()

    def get_lyrics(self, query):
        # full lyrics or random verse?
        if query[-1] == 'full':
            full = True
            query = query[:-1]
        else:
            full = False

        song_url = None

        # request for a specific song
        if query[0] == 'song':
            query = query[1:]

            if 'by' in query:
                song, artist = Lyrics._re_by.split(' '.join(query))
            else:
                song = query
                artist = None

            url = Lyrics._search
            opts = Lyrics._opts
            opts['q'] = song

            page = self.ua.fetch(url=url, opts=opts)
            soup = BeautifulSoup(page)

            for cell in soup.findAll('td', attrs={'class': 'lyric'}):
                link = cell.find('a')
                link.find('b').extract()
                cell_title = str(link.contents[0])
                cell_artist, cell_title = Lyrics._re_dash.split(cell_title)
                if artist is None or cell_artist.lower() == artist:
                    song_url = str(link['href'])
                    break

        # request for a random song from an artist
        else:
            url = Lyrics._artist_songs
            url = url.replace('SECTION', query[0][0])
            url = url.replace('ARTIST', '+'.join(query))
            page = self.ua.fetch(url)
            soup = BeautifulSoup(page)
            songs = []
            for cell in soup.findAll('td', attrs={'class': 'lyric'}):
                link = cell.find('a')
                link.find('b').extract()
                cell_title = str(link.contents[0])
                songs.append(str(link['href']))

            if songs:
                song_url = random.choice(songs)

        if song_url:
            page = self.ua.fetch(song_url)
            soup = BeautifulSoup(page)
            content = soup.find('div', attrs={'id': 'content'})
            [div.extract() for div in content.findAll('div')]
            [link.extract() for link in content.findAll('a')]
            [script.extract() for script in content.findAll('script')]
            lines = [str(line) for line in content.contents]
            data = ''.join(lines)
            data = Lyrics._newline.sub('', data)
            data = Lyrics._leadbreak.sub('', data)
            data = Lyrics._endbreak.sub('', data)
            lines = Lyrics._break.split(data)
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
                verse = Lyrics._whitespace.sub(' ', verse)
                verses[i] = verse


            if full:
                return '\n'.join(verses)
            else:
                return random.choice(verses)

        else:
            return "Couldn't find a match for that query"


class Main(Base):
    enabled = True
    pattern = re.compile(r'^\s*sing\s+(.+)$')
    require_addressing = True


    help = 'sing (<artist>|song <song> [by <artist>]) [full] - lyrics'

    def __init__(self, madcow=None):
        self.lyrics = Lyrics()

    def response(self, **kwargs):
        nick = kwargs['nick']
        query = kwargs['args'][0].lower().split()
        return self.lyrics.get_lyrics(query)

        try:
            return self.lyrics.get_lyrics(query)
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
