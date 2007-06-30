#!/usr/bin/env python

"""
NOTE: This is the template for creating your own user modules.  Copy this file
to something unique (it must end with .py!).  Edit the __init__ object.  This is
where you set what regular expression will trigger the process() function when run
within the bot, whether it should spawn a new thread when running response(), and whether
addressing is required.

The response() function is where your script goes, it should return a response.
"""

import sys
import re

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('keyword\s+(\S+)')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = None				# Put your usage line here as a string

	# function to generate a response
	def response(self, nick, args):
		try:
			pass
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return '%s: I failed to perform that lookup' % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
