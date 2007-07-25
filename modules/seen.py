#!/usr/bin/env python

# Keep track of what people last said

import sys
import re
import anydbm
import time
import os

# class for this module
class match(object):
	def __init__(self, dir=None, ns='default', config=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^(.+)$')	# regular expression that needs to be matched
		self.requireAddressing = False			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'seen <nick> - query bot about last time someone was seen speaking'

		if dir is None: dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
		self.file = dir + '/data/db-%s-seen' % ns
		self.seen = re.compile('^\s*seen\s+(\S+)\s*$', re.I)

	def get(self, user):
		user = user.lower()
		db = anydbm.open(self.file, 'c', 0640)
		try:
			packed = db[user]
			channel, last, message = packed.split('/', 2)

			seconds = int(time.time() - float(last))
			last = '%s second%s' % (seconds, 's' * (seconds != 1))

			minutes = seconds / 60
			seconds = seconds % 60
			if minutes: last = '%s minute%s' % (minutes, 's' * (minutes != 1))

			hours = minutes / 60
			minutes = minutes % 60
			if hours: last = '%s hour%s' % (hours, 's' * (hours != 1))

			days = hours / 24
			hours = hours % 24
			if days: last = '%s day%s' % (days, 's' * (days != 1))

			return message, channel, last
		except Exception, e:
			return None, None, None

	def set(self, nick, channel, message):
		packed = '%s/%s/%s' % (channel, time.time(), message)
		db = anydbm.open(self.file, 'c', 0640)
		db[nick.lower()] = packed
		db.close()

	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick']
		channel = kwargs['channel']
		line = kwargs['args'][0]

		try:
			self.set(nick, channel, line)

			match = self.seen.search(line)
			if not match: return

			user = match.group(1)
			message, channel, last = self.get(user)
			if not message:
				return "%s: I haven't seen %s say anything plz" % (nick, user)

			return '%s: %s was last seen %s ago on %s saying "%s"' % (nick, user, last, channel, message)

		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response(nick='testUser', args=argv, channel='#test')

	return 0

if __name__ == '__main__': sys.exit(main())
