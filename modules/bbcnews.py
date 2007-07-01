#!/usr/bin/env python

# This fuction is designed to serach the BBC News website and report the number one result.

import sys
import re
import urllib
from include import rssparser

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('bbcnews\s+(.*)')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'bbcnews <String> - Searches the BBC News Website' # Put your usage line here as a string
	
	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick']
		args = kwargs['args']

		try:
			try:
				url = 'http://newsapi.bbc.co.uk/feeds/search/news/' + urllib.quote(args[0])
				if args[0] == 'headline':
					url = 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/world/rss.xml'
			except:
				url = 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/world/rss.xml'
							
			try:
				res = int(args[1]) - 1
			except:
				res = 0
				
			doc = urllib.urlopen(url).read()			
			feed = rssparser.parse(url)
			rurl = feed['items'][res]['link']
			rtitle = feed['items'][res]['title']
			rsum = feed['items'][res]['description']
			
			
			return rurl + "\r" + rtitle + "\r" + rsum + "\r"
			
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: Looks like the BBC aren\'t co-operating today.' % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
