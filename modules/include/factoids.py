#!/usr/bin/env python

"""
$Id: factoids.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

This implements the infobot factoid database work-a-like
"""

import sys
import re
import os
import anydbm
import random

# class for this module
class Factoids(object):
	def __init__(self, dir = None):
		if dir is None: dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		self.dir = dir

		self.qmark = re.compile('\s*\?+\s*$')
		self.isare = re.compile('^(.+?)\s+(is|are)\s+(.+)\s*$', re.I)
		self.query = re.compile('^(?:who|what|where|when|why|how|wtf)', re.I)
		self.ors   = re.compile('\s*\|\s*')
		self.reply = re.compile('^<reply>\s*(.+)', re.I)
		self.also  = re.compile('^\s*also\s+', re.I)
		self.isor  = re.compile('^\s*\|')
		self.forget = re.compile('forget[:\-, ]+(.+)$', re.I)

	def dbFile(self, type):
		return self.dir + '/db-factoids-' + type.lower()

	def get(self, type, key):
		db = anydbm.open(self.dbFile(type), 'c', 0640)
		val = db.get(key.lower())
		db.close()
		return val

	def set(self, type, key, val):
		db = anydbm.open(self.dbFile(type), 'c', 0640)
		db[key.lower()] = val
		db.close()
		return None

	def unset(self, key):
		forgot = 0
		for type in ['is', 'are']:
			db = anydbm.open(self.dbFile(type), 'c', 0640)
			if db.has_key(key.lower()):
				del db[key.lower()]
				forgot += 1
			db.close()

		if forgot == 0:
			return False
		else:
			return True

	def check(self, nick, addressed, correction, message):
		try:
			# remove dubious whitespace
			message = message.strip()

			# see if we're trying to remove an entry
			forget = self.forget.search(message)
			if addressed is True and forget is not None:
				key = self.forget.sub('', forget.group(1))


				forgetResult = self.unset(key)

				if forgetResult is True:
					return 'OK, %s' % nick
				else:
					return '%s: nothing to forget..' % nick



			# strip off trailing qmark, which indicates a question, generally
			if self.qmark.search(message):
				message = self.qmark.sub('', message)
				question = True
			else:
				question = False


			# split up phrase by is/are seperator
			isare = self.isare.search(message)
			if isare is not None:
				key, type, val = isare.groups()

				# the ispart is actually a query
				if self.query.search(key):
					key = val
					val = None
					question = True

			# XXX this should test both, if is doesn't work, use are :P
			# foo? use 'is' database, ambiguous
			elif question is True:
				key = message
				type = 'is'
				question = True
			else:
				return


			### QUERY
			if question is True:
				val_is = self.get('is', key)
				val_are = self.get('are', key)

				if val_is is None and val_are is None:
					val = None
				elif val_is is not None and type == 'is':
					val = val_is
				elif val_are is not None and type == 'are':
					val = val_are
				elif val_is is not None:
					val = val_is
					type = 'is'
				elif val_are is not None:
					val = val_are
					type = 'are'

				if val is None:
					if addressed is True:
						return 'I have no idea, %s' % nick
				else:
					# get a random selection from | delimited list
					val = random.choice(self.ors.split(val))

					# <reply> foo should just print 'foo'
					reply = self.reply.search(val)
					if reply is not None:
						return reply.group(1)
					else:
						response = '%s %s %s' % (key, type, val)
						if addressed:
							response = '%s: %s' % (nick, response)
						return response

			### SET
			else:
				# see if we're trying to append
				if self.also.search(val):
					val = self.also.sub('', val)
					also = True
				else:
					also = False

				# see if it's already set
				setVal = self.get(type, key)

				if ((setVal is not None) and (also is True)):
					if self.isor.search(val):
						val = '%s %s' % (setVal, val)
					else:
						val = '%s or %s' % (setVal, val)
				elif ((setVal is not None) and (correction is False)):
					if addressed: return '%s: But %s %s %s' % (nick, key, type, setVal)
					else: return

				self.set(type, key, val)
				if addressed: return 'OK, %s' % nick

		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)

# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]

	a = argv[0] == 'True' and True or False
	c = argv[1] == 'True' and True or False
	f = Factoids('../..')
	print f.check('testUser', a, c, argv[2])

	return 0

if __name__ == '__main__': sys.exit(main())
