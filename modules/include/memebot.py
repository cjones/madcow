#!/usr/bin/env python

# Watch URLs in channel, punish people for living under a rock

import sys
import re
import os
import urlparse
import datetime
from pysqlite2 import dbapi2 as sqlite
from sqlobject import *
import random

# object model
class url(SQLObject):
	url = StringCol(alternateID = True)
	clean = StringCol(alternateID = True)
	author = ForeignKey('author')
	channel = ForeignKey('channel')
	citations = IntCol(default = 0)
	posted = DateTimeCol(default = datetime.datetime.now)

	def truncated_url(self):
		if (len(self.url) > 48):
			return self.url[:48] + ' ... ' + self.url[-4:]
		else:
			return self.url

	turl = property(truncated_url)

class author(SQLObject):
	name = StringCol(alternateID = True)
	urls = MultipleJoin('url')
	pointsNew = IntCol(default = 0)
	pointsOld = IntCol(default = 0)
	pointsCredit = IntCol(default = 0)

class channel(SQLObject):
	name = StringCol(alternateID = True)
	urls = MultipleJoin('url')


# class for this module
class MemeBot(object):
	def __init__(self):
		self.matchURL = re.compile('(http://\S+)', re.I)
		self.dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		self.file = self.dir + '/db-memes'

		sqlhub.processConnection = connectionForURI('sqlite://' + self.file)
		url.createTable(ifNotExists = True)
		author.createTable(ifNotExists = True)
		channel.createTable(ifNotExists = True)

		self.riffs = [
			'memeriffs=OLD MEME ALERT!',
			'omg, SO OLD!',
			'Welcome to yesterday.',
			'been there, done that.',
			'you missed the mememobile.',
			'oldest. meme. EVAR.',
			'jesus christ you suck.',
			'you need a new memesource, bucko.',
			'that was funny the first time i saw it.',
		]


	def cleanURL(self, url):
		uri = list(urlparse.urlparse(url))
		uri[1] = uri[1].lower()
		if uri[2] == '': uri[2] = '/'
		uri[5] = ''
		return urlparse.urlunparse(uri)

	def getScoreForAuthor(self, a):
		return	a.pointsNew    *  1 + \
			a.pointsOld    * -2 + \
			a.pointsCredit *  2

	def top10(self):
		scores = [(a.name, self.getScoreForAuthor(a)) for a in author.select()]
		return sorted(scores, lambda x, y: cmp(y[1], x[1]))[:10]


	# function to generate a response
	def check(self, nick, chan, message, addressed):
		nick = nick.lower()

		if addressed is True and 'score' in message:
			scores = []
			for i, data in enumerate(self.top10()):
				name, score = data
				scores.append('#%s: %s (%s)' % (i + 1, name, score))
			return ', '.join(scores)
			


		match = self.matchURL.search(message)
		if match is None: return
		orig = match.group(1)
		clean = self.cleanURL(orig)

		try: me = author.byName(nick)
		except SQLObjectNotFound: me = author(name = nick)

		try:
			# old meme
			old = url.byClean(clean)

			# chew them out unless its my own
			if old.author.name != nick:
				response = 'first posted by %s on %s' % (old.author.name, old.posted)
				riff = random.choice(self.riffs)
				old.author.pointsCredit = old.author.pointsCredit + 1
				me.pointsOld = me.pointsOld + 1
				old.citations = old.citations + 1
				return '%s %s' % (riff, response)


		except SQLObjectNotFound:
			try: c = channel.byName(chan)
			except SQLObjectNotFound: c = channel(name = chan)

			url(url = orig, clean = clean, author = me, channel = c)

			me.pointsNew = me.pointsNew + 1

		except Exception, e:
			print >> sys.stderr, 'error: %s' % e

		return



# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = MemeBot()
	print obj.check('cj_', '#hugs', argv[0], True)

	return 0

if __name__ == '__main__': sys.exit(main())
