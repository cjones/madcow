#!/usr/bin/env python

# Interface for getting really stupid IRC quotes

import sys
import re
import urllib
import random
from include import utils

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*(bash|qdb)(?:\s+(\S+))?', re.I)
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = '<bash|qdb> [#|query] - get stupid IRC quotes, or random'

		self.sources = {
			'bash'	: {
				'random'	: 'http://www.bash.org/?random',
				'bynum'		: 'http://www.bash.org/?num',
				'search'	: 'http://www.bash.org/?search=query&show=100',
				'entries'	: re.compile('<p class="qt">(.*?)</p>', re.DOTALL),
			},
			'qdb'	: {
				'random'	: 'http://qdb.us/random',
				'bynum'		: 'http://qdb.us/num',
				'search'	: 'http://qdb.us/?search=query&limit=100&approved=1',
				'entries'	: re.compile('<td[^>]+><p>(.*?)</p>', re.DOTALL),
			},
		}

		self.num = re.compile('num')
		self.query = re.compile('query')

	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick']
		args = kwargs['args']

		try:
			source = self.sources[args[0]]

			try: query = args[1]
			except: query = None

			try: num = int(query); query = None
			except: num = None

			if num:
				url = source['bynum']
				url = self.num.sub(str(num), url)
			elif query:
				url = source['search']
				url = self.query.sub(query, url)
			else:
				url = source['random']

			doc = urllib.urlopen(url).read()
			entries = source['entries'].findall(doc)

			if query:
				m = re.compile(query, re.I)
				entries = [entry for entry in entries if m.search(entry)]

			if len(entries) > 1:
				random.seed()	# still need this with threads?
				entry = random.choice(entries)
			else:
				entry = entries[0]

			return utils.stripHTML(entry)

		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: Having some issues, make some stupid quotes yourself' % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
