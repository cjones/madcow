#!/usr/bin/env python

"""
get the current woot - author: Twid
"""

import sys
import re
import urllib
import string
from include import rssparser
from include import utils

class currency(float):
    def __init__(self,amount):
        self.amount = amount
    def __str__(self):
        temp = "%.2f" % self.amount
        profile = compile(r"(\d)(\d\d\d[.,])")
        while 1:
            temp, count = subn(profile,r"\1,\2",temp)
            if not count: break
        return temp

# class for this module
class match(object):
	def __init__(self):
		self.enabled = True				# True/False - enabled?
		self.pattern = re.compile('(?:woot)(?:\s+(\S+))?')
		self.requireAddressing = True			# True/False - require addressing?
		self.thread = True				# True/False - should bot spawn thread?
		self.wrap = True				# True/False - wrap output?
		self.help = 'woot - get latest offer from woot.com'

		self.baseURL = 'http://woot.com'
		self.max = 200
	
	# function to generate a response
	def response(self, nick, args):
		try:
	
			url = self.baseURL + '/Blog/Rss.aspx'
			feed = rssparser.parse(url)

			# get latest entry and their homepage url
			title = string.split(feed['items'][0]['title'])
			offer = string.join(title[:-2])
			
			try:
				price = "$%s" % string.atof(title[-1])
			except:
				price = ''

			longdescription = feed['items'][0]['description']
			page = feed['items'][0]['link']

			# strip out html
			longdescription = string.lstrip(utils.stripHTML(longdescription))

			# these can get absurdly long
			longdescription = longdescription[:self.max] + ' ...'

			return '%s: %s\n[%s]\n%s' % (offer, price, page, longdescription)
		except Exception, e:
			print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
			return "%s: Couldn't load the page woot returned D:" % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
	if argv is None: argv = sys.argv[1:]
	obj = match()
	print obj.response('testUser', argv)

	return 0

if __name__ == '__main__': sys.exit(main())
