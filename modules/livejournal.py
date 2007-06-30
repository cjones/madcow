#!/usr/bin/env python

"""
$Id: livejournal.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

get a random lj
"""

import sys
import re
import urllib
from include import rssparser
from include import utils

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('(?:livejournal|lj)(?:\s+(\S+))?')
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'lj [user] - get latest entry to an lj, omit user for a random one'

		self.baseURL = 'http://livejournal.com'
		self.max = 800
	
	# function to generate a response
	def response(self, nick, args):
		try:
			try: user = args[0]
			except: user = None

			if user is None:
				# load random page, will redirect
				url = self.baseURL + '/random.bml'
				doc = urllib.urlopen(url).read()

				# find username and load their rss feed with mark pilgrim's rssparser
				user = re.search('"currentJournal": "(.*?)"', doc).group(1)

			url = '%s/users/%s/data/rss' % (self.baseURL, user)
			feed = rssparser.parse(url)

			# get latest entry and their homepage url
			entry = feed['items'][0]['description']
			page = feed['channel']['link']

			# strip out html
			entry = utils.stripHTML(entry)

			# detect unusual amounts of high ascii, probably russian journal
			if utils.isUTF8(entry):
				return '%s: Russian LJ :(' % nick

			# these can get absurdly long
			entry = entry[:self.max]

			return '%s: [%s] %s' % (nick, page, entry)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: Couldn't load the page LJ returned D:" % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
