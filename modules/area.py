#!/usr/bin/env python

"""
This module looks up area codes and returns the most likely city
"""

import sys
import re
import urllib2
import cookielib
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*area(?:\s+code)?\s+(\d+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'area <areacode> - what city does it belong to'

        self.baseURL = 'http://www.melissadata.com/lookups/phonelocation.asp'
        self.match = re.compile("<tr><td><A[^>]+>(.*?)</a></td><td>(.*?)</td><td align=center>\d+</td></tr>")

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            # create an opener object that supports cookies
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))

            # make bogus request to get cookie saved.. stupid website
            opener.open(urllib2.Request(self.baseURL))

            # real request..
            doc = opener.open(urllib2.Request('%s?number=%s' % (self.baseURL, args[0]))).read()
            city, state = self.match.search(doc).groups()
            city = ' '.join([x.lower().capitalize() for x in city.split()])
            return '%s: %s = %s, %s' % (nick, args[0], city, state)
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: I couldn't look that up for some reason.  D:" % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
