#!/usr/bin/env python

"""
Get doomsday clock status from the bulletin
"""

import sys
import re
import urllib
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*doomsday')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'doomsday - get doomsday clock status from the bulletin'

        self.url = 'http://www.thebulletin.org/minutes-to-midnight/'
        self.time = re.compile('href="/minutes-to-midnight/">(.*?)</a>')

    def response(self, **kwargs):
        nick = kwargs['nick']

        try:
            doc = urllib.urlopen(self.url).read()
            time = self.time.search(doc).group(1)
            return '%s: %s' % (nick, time)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Couldn't get doomsday info, maybe the world ended?" % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'])
