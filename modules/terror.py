#!/usr/bin/env python

# Get the current TERRA level

import sys
import re
import urllib

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('terror')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'terror - get DHS terra threat level'

		self.url = 'http://www.dhs.gov/dhspublic/getAdvisoryCondition'
		self.level = re.compile('<THREAT_ADVISORY CONDITION="(\w+)" />')
		self.colors = {	'severe'	: 5,
				'high'		: 4,
				'elevated'	: 8,
				'guarded'	: 12,
				'low'		: 9,	}

	# function to generate a response
	def response(self, nick, args):
		try:
			doc = urllib.urlopen(self.url).read()
			level = self.level.search(doc).group(1)
			color = self.colors[level.lower()]
			return '\x03%s,1\x16\x16%s\x0f' % (color, level)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: No response.. maybe terrorists blew up the DHS" % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
