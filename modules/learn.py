#!/usr/bin/env python

"""
$Id: learn.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

Module to handle learning
"""

import sys
import re
import anydbm
import os

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('learn\s+(\S+)\s+(.+)')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?

		self.dbfile = os.path.abspath(os.path.dirname(sys.argv[0]) + '/db-locations')

	def lookup(self, nick):
		db = anydbm.open(self.dbfile, 'c', 0640)
		try: location = db[nick.lower()]
		except: location = None
		db.close()
		return location

	def set(self, nick, location):
		db = anydbm.open(self.dbfile, 'c', 0640)
		db[nick.lower()] = location
		db.close()

	# function to generate a response
	def response(self, nick, args):
		if len(args) == 1:
			return self.lookup(args[0])
		else:
			self.set(args[0], args[1])
			return '%s: I learned that %s is in %s' % (nick, args[0], args[1])


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
