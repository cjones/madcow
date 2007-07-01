#!/usr/bin/env python

# Implement Grufti trigger/response spam

import sys
import re
import os
import random

# class for this module
class match(object):
	def __init__(self, config=None, ns='default', dir=None):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('(.*)')	# regular expression that needs to be matched
		self.requireAddressing = False			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?

		if dir is None: dir = os.path.abspath(os.path.dirname(sys.argv[0]))
		file = dir + '/grufti-responses.txt'

		try:
			fi = open(file)
			doc = fi.read()
			fi.close()

			self.data = []

			for obj in re.compile('%match\s+(.*?)%end[\r\n]?', re.DOTALL + re.IGNORECASE).split(doc):
				responses = obj.splitlines()
				if len(responses) < 2: continue
				
				matchString, responses = responses[0], responses[1:]
				matches = re.compile('\s*,\s*').split(matchString)

				self.data.append((matches, responses))
		except:
			self.enabled = False


	# function to generate a response
	def response(self, *args, **kwargs):
		nick = kwargs['nick']
		args = kwargs['args']
		if self.enabled is False: return

		line = ' '.join(args)
		for matches, responses in self.data:
			for match in matches:
				if re.compile(match, re.I).search(line):
					return random.choice(responses)


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match(dir = '..')
	print obj.response(nick='testUser', args=argv)

	return 0

if __name__ == '__main__': sys.exit(main())
