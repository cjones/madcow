#!/usr/bin/env python

"""
$Id: nslookup.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

Perform DNS lookups
"""

import sys
import re
import socket

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('nslookup\s+(\S+)')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'nslookup <ip|host> - perform DNS lookup'

	# function to generate a response
	def response(self, nick, args):
		query = args[0]
		if re.search('^(\d+\.){3}\d+$', query):
			try: response = socket.gethostbyaddr(query)[0]
			except: response = 'No hostname for that IP'
		else:
			try: response = socket.gethostbyname(query)
			except: response = 'No IP for that hostname'

		return '%s: %s' % (nick, response)


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
