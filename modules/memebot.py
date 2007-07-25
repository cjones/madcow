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
from include.throttle import Throttle

# object model
class url(SQLObject):
	url = StringCol(alternateID = True)
	clean = StringCol(alternateID = True)
	author = ForeignKey('author')
	channel = ForeignKey('channel')
	citations = IntCol(default = 0)
	posted = DateTimeCol(default = datetime.datetime.now)
	comments = MultipleJoin('comments')

	def truncated_url(self):
		if (len(self.url) > 48):
			return self.url[:48] + ' ... ' + self.url[-4:]
		else:
			return self.url

	turl = property(truncated_url)

class author(SQLObject):
	name = StringCol(alternateID = True)
	urls = MultipleJoin('url')
	comments = MultipleJoin('comments')
	pointsNew = IntCol(default = 0)
	pointsOld = IntCol(default = 0)
	pointsCredit = IntCol(default = 0)

class channel(SQLObject):
	name = StringCol(alternateID = True)
	urls = MultipleJoin('url')

class comments(SQLObject):
	text = StringCol()
	author = ForeignKey('author')
	url = ForeignKey('url')



# class for this module
class match(object):
	def __init__(self, ns='default', config=None, dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^(.+)$')	# regular expression that needs to be matched
		self.requireAddressing = False			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'score [name,range] - get memescore for name/range, empty for top10'

		if dir is None: dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
		file = dir + '/data/db-%s-memes' % ns

		self.matchURL = re.compile('(http://\S+)', re.I)
		self.scoreRequest = re.compile(r'^\s*score(?:(?:\s+|[:-]+\s*)(\S+?)(?:\s*-\s*(\S+))?)?\s*$', re.I)
		self.colonHeader = re.compile(r'^\s*(.*?)\s*:\s*$')
		self.throttle = Throttle()

		sqlhub.processConnection = connectionForURI('sqlite://' + file)
		url.createTable(ifNotExists = True)
		author.createTable(ifNotExists = True)
		channel.createTable(ifNotExists = True)
		comments.createTable(ifNotExists = True)

		self.riffs = [
			'OLD MEME ALERT!',
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

	# XXX magic numbers, move to config
	def getScoreForAuthor(self, a):
		return	a.pointsNew    *  1 + \
			a.pointsOld    * -2 + \
			a.pointsCredit *  2

	def getScores(self):
		scores = [(a.name, self.getScoreForAuthor(a)) for a in author.select()]
		scores = sorted(scores, lambda x, y: cmp(y[1], x[1]))
		return scores


	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick'].lower()
		chan = kwargs['channel']
		addressed = kwargs['addressed']
		message = kwargs['args'][0]

		if addressed is True:
			try:
				x, y = self.scoreRequest.search(message).groups()
				scores = self.getScores()
				size = len(scores)

				if x is None:
					scores = scores[:10]
					x = 1
				elif x.isdigit() is True:
					x = int(x)
					if x == 0: x = 1
					if x > size: x = size

					if y is not None and y.isdigit() is True:
						y = int(y)
						if y > size: y = size
						scores = scores[x-1:y]
					else:
						scores = [scores[x-1]]

				else:
					for i, data in enumerate(scores):
						name, score = data
						if name.lower() == x.lower():
							scores = [scores[i]]
							x = i+1
							break

				out = []
				for i, data in enumerate(scores):
					name, score = data
					out.append('#%s: %s (%s)' % (i + x, name, score))
				return ', '.join(out)
				
			except:
				pass



		match = self.matchURL.search(message)
		if match is None: return

		event = self.throttle.registerEvent(name='memebot', user=nick)
		if event.isThrottled() is True:
			if event.warn() is True:
				return '%s: Stop abusing me plz.' % nick
			else:
				return



		orig = match.group(1)
		clean = self.cleanURL(orig)

		comment1, comment2 = re.split(re.escape(orig), message)
		try: comment1 = self.colonHeader.search(comment1).group(1)
		except: pass

		comment1 = comment1.strip()
		comment2 = comment2.strip()

		try: me = author.byName(nick)
		except SQLObjectNotFound: me = author(name = nick)

		try:
			# old meme
			old = url.byClean(clean)

			if len(comment1) > 0: comments(url=old, text=comment1, author=me)
			if len(comment2) > 0: comments(url=old, text=comment2, author=me)

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

			urlid = url(url = orig, clean = clean, author = me, channel = c)

			if len(comment1) > 0: comments(url=urlid, text=comment1, author=me)
			if len(comment2) > 0: comments(url=urlid, text=comment2, author=me)

			me.pointsNew = me.pointsNew + 1

		except Exception, e:
			print >> sys.stderr, 'error: %s' % e

		return



# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match(ns='madcow')
	print obj.response(nick='testUser', channel='#test', args=[argv[0]], addressed=True)

	return 0

if __name__ == '__main__': sys.exit(main())
