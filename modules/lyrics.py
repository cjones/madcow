#!/usr/bin/env python

"""
Get random lyrics for artist/song
"""

import sys
import re
import urllib
import random
import cookielib, urllib, urllib2

class match(object):
	baseURL = 'http://www.lyricsfreak.com'
	reTables = re.compile('<table.*?>(.*?)</table>', re.DOTALL)
	reRows = re.compile('<tr.*?>(.*?)</tr>', re.DOTALL)
	reSongURL = re.compile('<a href="(.*?)" title="(.*?) lyrics">', re.DOTALL)
	reLyrics = re.compile('<div id="content".*?>(.*?)</div>', re.DOTALL)
	reNewLine = re.compile(r'[\r\n]+')
	reDoubleBreak = re.compile('<br><br>')
	reLineBreak = re.compile('<br>')
	reSearchSongURL = re.compile('<a href="(.*?)"><b.*?</b>(.*?) - (.*?)</a>', re.DOTALL)

	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*sing\s+(.+)$')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'sing [song] <artist/song> - grab random lyrics'

		cj = cookielib.CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]
		self.opener = opener


	def response(self, *args, **kwargs):
		nick = kwargs['nick']
		query = kwargs['args'][0].lower().split()

		if query[0] == 'song':
			url = match.baseURL + '/search.php'
			query = ' '.join(query[1:])
			opts = {
				'type': 'title',
				'q': query,
				'sa.x': 21,
				'sa.y': 20,
				'sa': 'Search',
			}
			req = urllib2.Request(url, urllib.urlencode(opts))
			req.add_header('Referer', url)
			doc = self.opener.open(req).read()
			rows = [r for r in match.reRows.findall(match.reTables.findall(doc)[1]) if 'class="lyric"' in r]

			songs = {}
			for row in rows:
				url, artist, song = match.reSearchSongURL.search(row).groups()
				songs[url] = song

			url = random.choice(songs.keys())
			song = songs[url]
		else:
			query = '+'.join(query)
			url = '%s/%s/%s/lyrics.html' % (match.baseURL, query[0], query)
			doc = urllib.urlopen(url).read()
			rows = [r for r in match.reRows.findall(match.reTables.findall(doc)[1]) if 'class="lyric"' in r]
			songs = [row for row in rows if 'id="star"' in row]

			if len(songs) == 0:
				songs = [row for row in rows if 'starZero' in row]
				if len(songs) == 0:
					raise Exception('no songs')

			url, song = match.reSongURL.search(random.choice(songs)).groups()

		return '%s: %s' % (song, self.getSongLyrics(url))

		"""
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: Who?' % nick
		"""

	def getSongLyrics(self, url):
		doc = urllib.urlopen(url).read()

		lyrics = match.reLyrics.search(doc).group(1)
		lyrics = match.reNewLine.sub('', lyrics)
		blocks = match.reDoubleBreak.split(lyrics)
		block = random.choice(blocks)
		block = match.reLineBreak.sub(' // ', block)

		return block


def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
