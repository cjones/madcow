#!/usr/bin/env python

"""
$Id: chp.py,v 1.1.1.1 2007/06/25 23:09:20 cjones Exp $

Get traffic info from CHP website (bay area only)
"""

import sys
import re
import urllib
from include import utils

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('chp\s+(.+)', re.I)
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = False				# True/False - wrap output?
		self.help = 'chp <highway> - look for CHP reports for highway, such as 101'

		self.url = 'http://cad.chp.ca.gov/sa_list.asp?centerin=GGCC&style=l'
		self.incidents = re.compile('<tr>(.*?)</tr>', re.DOTALL)
		self.data = re.compile('<td class="T".*?>(.*?)</td>')
		self.clean = re.compile('[^0-9a-z ]', re.I)

	# function to generate a response
	def response(self, nick, args):
		try:
			check = self.clean.sub('', args[0])
			check = re.compile(check, re.I)

			results = []
			for i in self.incidents.findall(urllib.urlopen(self.url).read()):
				data = [utils.stripHTML(c) for c in self.data.findall(i)][1:]
				if len(data) != 4: continue
				if check.search(data[2]):
					results.append('=> %s: %s - %s - %s' % (data[0], data[1], data[2], data[3]))

			if len(results) > 0:
				return '\n'.join(results)
			else:
				return '%s: No incidents found' % nick

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
