#!/usr/bin/env python

# Get doomsday clock status from the bulletin

import sys
import re
import urllib

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('doomsday')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'doomsday - get doomsday clock status from the bulletin'

		self.url = 'http://www.thebulletin.org/minutes-to-midnight/'
		self.time = re.compile('href="/minutes-to-midnight/">(.*?)</a>')

	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick']
		args = kwargs['args']
		try:
			doc = urllib.urlopen(self.url).read()
			time = self.time.search(doc).group(1)
			return '%s: %s' % (nick, time)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: Couldn't get doomsday info, maybe the world ended?" % nick



# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
