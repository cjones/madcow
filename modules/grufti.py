#!/usr/bin/env python

# Implement Grufti trigger/response spam

import sys
import re
import os
import random

# class for this module
class match(object):
	reMatchBlocks = re.compile('%match\s+(.*?)%end', re.DOTALL)
	reCommaDelim = re.compile('\s*,\s*')
	rePipeDelim = re.compile('\s*\|\s*')
	reToken = re.compile('({{\s*(.*?)\s*}})')

	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('^(.+)$')	# regular expression that needs to be matched
		self.requireAddressing = False			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?

		self.data = []

		if dir is None: dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		file = dir + '/grufti-responses.txt'

		try:
			fi = open(file)
			doc = fi.read()
			fi.close()

			for block in self.reMatchBlocks.findall(doc):
				responses = block.splitlines()
				matchString = responses.pop(0)
				if len(responses) == 0: continue
				matches = []
				for match in self.reCommaDelim.split(matchString):
					matches.append(re.compile(r'\b' + re.escape(match) + r'\b', re.I))

				self.data.append((matches, responses))

		except:
			self.enabled = False

	def parseTokens(self, response):
		output = response
		for token, wordString in self.reToken.findall(response):
			word = random.choice(self.rePipeDelim.split(wordString))
			output = re.sub(re.escape(token), word, output, 1)

		return output

	# function to generate a response
	def response(self, *args, **kwargs):
		try:
			nick = kwargs['nick']
			args = kwargs['args']

			for matches, responses in self.data:
				for match in matches:
					if match.search(args[0]) is not None:
						return self.parseTokens(random.choice(responses))

		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match(dir = '..')
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
