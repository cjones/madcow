#!/usr/bin/env python

"""
This fuction is designed to serach the BBC News website and report the number one result.
"""

import sys
import re
import urllib
from include import rssparser
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*bbcnews(?:\s+(.+))?')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'bbcnews <String> - Searches the BBC News Website'
    
    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        if len(args) == 0:
            args = ['headline']

        try:
            try:
                url = 'http://newsapi.bbc.co.uk/feeds/search/news/' + urllib.quote(args[0])
                if args[0] == 'headline':
                    url = 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/world/rss.xml'
            except:
                url = 'http://newsrss.bbc.co.uk/rss/newsonline_uk_edition/world/rss.xml'
                            
            try:
                res = int(args[1]) - 1
            except:
                res = 0
                
            doc = urllib.urlopen(url).read()            
            feed = rssparser.parse(url)
            rurl = feed['items'][res]['link']
            rtitle = feed['items'][res]['title']
            rsum = feed['items'][res]['description']
            
            
            return rurl + "\r" + rtitle + "\r" + rsum + "\r"
            
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: Looks like the BBC aren\'t co-operating today.' % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=sys.argv[1:])
    sys.exit(0)
