#!/usr/bin/env python

"""
$Id: bullshitr.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

Make up some nonsense about web-2.0, like the peole who run the sites do
"""

import sys
import re
import random

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('web.*2\.0')	# regular expression that needs to be matched
		self.requireAddressing = False			# True/False - require addressing?
		self.thread = False				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = None				# Put your usage line here as a string

		self.wordList = [
			[
				'aggregate', 'beta-test', 'integrate', 'capture', 'create',
				'design', 'disintermediate', 'enable', 'integrate', 'post',
				'remix', 'reinvent', 'share', 'syndicate', 'tag',
				'incentivize', 'engage', 'reinvent', 'harness', 'integrate',
			], [
				'AJAX-enabled', 'A-list', 'authentic', 'citizen-media',
				'Cluetrain', 'data-driven', 'dynamic', 'embedded', 'long-tail',
				'peer-to-peer', 'podcasting', 'rss-capable', 'semantic',
				'social', 'standards-compliant', 'user-centred',
				'user-contributed', 'viral', 'blogging', 'rich-client',
			], [
				'APIs', 'blogospheres', 'communities', 'ecologies', 'feeds',
				'folksonomies', 'life-hacks', 'mashups', 'network effects',
				'networking', 'platforms', 'podcasts', 'value', 'web services',
				'weblogs', 'widgets', 'wikis', 'synergies', 'ad delivery',
				'tagclouds',
			],
		]
	

	# function to generate a response
	def response(self, nick, args):
		try:
			words = ' '.join([random.choice(word) for word in self.wordList])
			return 'Web 2.0: %s' % words

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
