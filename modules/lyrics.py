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
            links = soup.findAll('a', attrs=Lyrics._links)
            artist = str(links[2].contents[0])
            song = str(links[3].contents[0])
            [br.extract() for br in soup.findAll('br')]
            [ul.extract() for ul in soup.findAll('ul')]
            cursor = soup.find('script', attrs={'src': '/media/agent.js'})
            lyrics = ['%s by %s:' % (song, artist)]
            while True:
                cursor = cursor.next
                line = str(cursor).strip()
                if len(line) == 0 or '<ul' in line:
                    break
                lyrics.append(line)
            return '\n'.join(lyrics)
        else:
            return "Couldn't find a match for that query"


class MatchObject(Base):

    def __init__(self, config=None, ns=_namespace, dir=_dir):
        self.config = config
        self.ns = ns
        self.dir = dir
        self.enabled = True
        self.pattern = re.compile(r'^\s*sing\s+(.+)$')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'sing (<artist>|song <song> [by <artist>]) [full] - lyrics'
        self.lyrics = Lyrics()

    def response(self, **kwargs):
        nick = kwargs['nick']
        query = kwargs['args'][0].lower().split()
        return self.lyrics.get_lyrics(query)

        try:
            return self.lyrics.get_lyrics(query)
        except Exception, e:
            return '%s: problem with query: %s' % (nick, e)


if __name__ == '__main__':
    mo = MatchObject()
    nick = os.environ['USER']
    args = ' '.join(sys.argv[1:])
    print mo.response(nick=nick, args=[args])
    sys.exit(0)
