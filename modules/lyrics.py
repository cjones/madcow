#!/usr/bin/env python

"""
Get random lyrics for artist/song
"""

import sys
import re
import urllib
import random

class match(object):
	baseURL = 'http://www.lyricsfreak.com'
	reTables = re.compile('<table.*?>(.*?)</table>', re.DOTALL)
	reRows = re.compile('<tr.*?>(.*?)</tr>', re.DOTALL)
	reSongURL = re.compile('<a href="(.*?)" title="(.*?) lyrics">', re.DOTALL)
	reLyrics = re.compile('<div id="content".*?>(.*?)</div>', re.DOTALL)
	reNewLine = re.compile(r'[\r\n]+')
	reDoubleBreak = re.compile('<br><br>')
	reLineBreak = re.compile('<br>')

	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*sing\s+(.+)$')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'sing <artist/song> - grab random lyrics'

	def response(self, *args, **kwargs):
		try:
			nick = kwargs['nick']
			query = '+'.join(kwargs['args'][0].split())

			url = '%s/%s/%s/lyrics.html' % (match.baseURL, query[0], query)
			doc = urllib.urlopen(url).read()


			rows = [row for row in match.reRows.findall(match.reTables.findall(doc)[1]) if 'class="lyric"' in row]
			songs = [row for row in rows if 'id="star"' in row]

			if len(songs) == 0:
				songs = [row for row in rows if 'starZero' in row]
				if len(songs) == 0:
					raise Exception, 'no songs'

			url, song = match.reSongURL.search(random.choice(songs)).groups()

			doc = urllib.urlopen(url).read()

			lyrics = match.reLyrics.search(doc).group(1)
			lyrics = match.reNewLine.sub('', lyrics)
			blocks = match.reDoubleBreak.split(lyrics)
			block = random.choice(blocks)
			block = match.reLineBreak.sub(' // ', block)
			block = '%s: %s' % (song, block)
			return block


		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: Who?' % nick


def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
