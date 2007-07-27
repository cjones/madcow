#!/usr/bin/env python

"""
Get lyrics from http://www.lyricsfreak.com/
"""

import sys
import re
import random
import urllib, urllib2, cookielib


class MatchObject(object):

    baseURL = 'http://www.lyricsfreak.com/'

    reTables = re.compile('<table.*?>(.*?)</table>', re.DOTALL)
    reRows = re.compile('<tr.*?>(.*?)</tr>', re.DOTALL)
    reSongLink = re.compile('href="(.*?)".*?>.*?</b>(.*?)</a>')
    reArtistDelim = re.compile('\s*-\s*')
    reLyrics = re.compile('<div id="content".*?>(.*?)</div>', re.DOTALL)
    reVerseBreak = re.compile('\s*<br>\s*<br>\s*')
    reLineBreak = re.compile('\s*<br>\s*')

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile(r'^\s*sing\s+(.+)$')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'sing (<artist> | song <song> [by <artist>]) [full] - get lyrics'

        # build opener
        cj = cookielib.CookieJar()
        ch = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(ch)
        opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
        self.opener = opener

    def request(self, url, opts=None, referer=None):
        if opts is not None:
            req = urllib2.Request(url, urllib.urlencode(opts))
        else:
            req = urllib2.Request(url)

        if referer is not None:
            req.add_header('Referer', referer)

        res = self.opener.open(req)
        data = res.read()
        return data

    def response(self, **kwargs):
        try:
            query = kwargs['args'][0].lower().split()

            if query[-1] == 'full':
                query = query[:-1]
                full = True
            else:
                full = False

            if query[0] == 'song':
                query = query[1:]
                type = 'song'

                if 'by' in query:
                    i = query.index('by')
                    query, artist = query[:i], query[i+1:]
                else:
                    artist = None

                query = ' '.join(query)
                url = MatchObject.baseURL + 'search.php'
                opts = {'type': 'title', 'q': query, 'sa.x': 21, 'sa.y': 20, 'sa': 'Search'}
                page = self.request(url, opts=opts, referer=url)

            else:
                artist = None
                query = '+'.join(query)
                url = MatchObject.baseURL + '%s/%s/lyrics.html' % (query[0], query)
                page = self.request(url, referer=MatchObject.baseURL)

            tables = MatchObject.reTables.findall(page)
            table = tables[1]
            rows = [row for row in MatchObject.reRows.findall(table) if 'class="lyric"' in row]

            songs = []
            for row in rows:
                url, title = MatchObject.reSongLink.search(row).groups()
                songs.append((url, title))

            if artist is not None:
                artist = map(re.escape, artist)
                artist = '\\s+'.join(artist)
                artist = re.compile(artist, re.I)

                filtered = []
                for url, title in songs:
                    songArtist, songName = MatchObject.reArtistDelim.split(title, 1)
                    if artist.search(songArtist):
                        filtered.append((url, title))

                songs = filtered

            if not songs:
                raise Exception, 'No results'

            url, title = random.choice(songs)
            page = self.request(url)
            lyrics = MatchObject.reLyrics.search(page).group(1)
            lyrics = lyrics.replace('\n', '')

            if full is False:
                verses = MatchObject.reVerseBreak.split(lyrics)
                lyrics = random.choice(verses)

            lyrics = MatchObject.reLineBreak.split(lyrics)
            for i, line in enumerate(lyrics):
                if len(line) == 0:
                    line = '//'
                elif line[-1].isalpha():
                    line += '.'
                lyrics[i] = line

            lyrics = ' '.join(lyrics)
            return '%s: %s' % (title, lyrics)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: Problem with that: %s' % (kwargs['nick'], e)


def main():
    print MatchObject().response(nick='testUser', args=[' '.join(sys.argv[1:])])
    return 0

if __name__ == '__main__':
    sys.exit(main())
