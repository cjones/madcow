#!/usr/bin/env python

"""
$Id: artfart.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

Get a random offensive ASCII art
"""

import sys
import re
import urllib
import re
from include import utils

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('artfart')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'artfart - displays some offensive ascii art'

		self.randomURL = 'http://www.asciiartfarts.com/random.cgi'
		self.art = re.compile('<pre>(.*?)</pre>', re.DOTALL)

	# function to generate a response
	def response(self, nick, args):
		try:
			doc = urllib.urlopen(self.randomURL).read()
			return utils.stripHTML(self.art.findall(doc)[1])
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: I had a problem with that, sorry." % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
