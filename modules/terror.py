#!/usr/bin/env python

"""
Get the current TERRA level
"""

import sys
import re
import urllib
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*terror')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'terror - get DHS terra threat level'

        self.url = 'http://www.dhs.gov/dhspublic/getAdvisoryCondition'
        self.level = re.compile('<THREAT_ADVISORY CONDITION="(\w+)" />')
        self.colors = {
            'severe': 5,
            'high': 4,
            'elevated': 8,
            'guarded': 12,
            'low': 9,
        }

    def response(self, **kwargs):
        nick = kwargs['nick']

        try:
            doc = urllib.urlopen(self.url).read()
            level = self.level.search(doc).group(1)
            color = self.colors[level.lower()]
            return '\x03%s,1\x16\x16%s\x0f' % (color, level)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: No response.. maybe terrorists blew up the DHS" % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'])
    sys.exit(0)
