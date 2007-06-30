#!/usr/bin/env python

# Look up drink mixing ingredients

import sys
import re
import urllib
from include import utils

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('drinks?\s+(.+)')	# regular expression that needs to be matched
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'drinks <drink name> - look up mixing instructions'

		self.baseURL = 'http://www.webtender.com'
		self.drink = re.compile('<A HREF="(/db/drink/\d+)">')

		self.title = re.compile('<H1>(.*?)<HR></H1>')
		self.ingredients = re.compile('<LI>(.*?CLASS=ingr.+)')
		self.instructions = re.compile('<H3>Mixing instructions:</H3>.*?<P>(.*?)</P>', re.DOTALL)

	# function to generate a response
	def response(self, nick, args):
		url = self.baseURL + '/cgi-bin/search?' + urllib.urlencode(
				{	'verbose'	: 'on',
					'name'		: args[0],	}
				)
		try:
			doc = urllib.urlopen(url).read()
			drink = self.drink.search(doc).group(1)
			doc = urllib.urlopen(self.baseURL + drink).read()

			title = self.title.search(doc).group(1)
			ingredients = self.ingredients.findall(doc)
			instructions = self.instructions.search(doc).group(1)

			response = '%s: %s - %s - %s' % (nick, title, ', '.join(ingredients), instructions)
			response = utils.stripHTML(response)

			return response

		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: Something ungood happened looking that up, sry" % nick



# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
