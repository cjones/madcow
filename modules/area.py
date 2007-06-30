#!/usr/bin/env python

# This module looks up area codes and returns the most likely city

import sys
import re
import urllib2
import cookielib

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^\s*area(?:\s+code)?\s+(\d+)')
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'area <areacode> - what city does it belong to'

		self.baseURL = 'http://www.melissadata.com/lookups/phonelocation.asp'
		self.match = re.compile("<tr><td><A[^>]+>(.*?)</a></td><td>(.*?)</td><td align=center>\d+</td></tr>")

	# function to generate a response
	def response(self, nick, args):
		try:
			# create an opener object that supports cookies
			opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

			# make bogus request to get cookie saved.. stupid website
			opener.open(urllib2.Request(self.baseURL))

			# real request..
			doc = opener.open(urllib2.Request('%s?number=%s' % (self.baseURL, args[0]))).read()
			city, state = self.match.search(doc).groups()
			city = ' '.join([x.lower().capitalize() for x in city.split()])
			return '%s: %s = %s, %s' % (nick, args[0], city, state)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: I couldn't look that up for some reason.  D:" % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
