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
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*woot(?:\s+(\S+))?')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'woot - get latest offer from woot.com'

        self.baseURL = 'http://woot.com'
        self.max = 200
    
    def response(self, **kwargs):
        nick = kwargs['nick']

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


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
