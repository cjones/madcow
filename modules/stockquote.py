#!/usr/bin/env python

# Get stock quote

import sys
import re
import urllib

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('(?:stocks?|quote)\s+([a-z0-9.-]+)', re.I)
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'quote <symbol> - get latest stock quote'

		self.company = re.compile('<td height="30" class="ygtb"><b>(.*?)</b>')
		self.lastTrade = re.compile('(Last Trade|Net Asset Value):</td><td class="yfnc_tabledata1"><big><b>(.*?)</b>')
		self.change = re.compile('Change:</td><td class="yfnc_tabledata1">(?:<img.*?alt="(.*?)">)? <b.*?>(.*?)</b>')

	# function to generate a response
	def response(self, nick, args):
		try:
			doc = urllib.urlopen('http://finance.yahoo.com/q?s=' + args[0]).read()
			company = self.company.search(doc).group(1)
			tag, lastTrade = self.lastTrade.search(doc).groups()
			change = self.change.search(doc)
			dir = change.group(1)
			change = change.group(2)
			if dir is not None:
				change = '%s %s' % (dir.lower(), change)
			else:
				change = None

			return '%s: %s - %s: %s, Change = %s' % (nick, company, tag, lastTrade, change)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: Couldn't look that up, guess the market crashed." % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
