#!/usr/bin/env python

"""
Summon people
"""

import sys
import re
import urllib
import learn
import os

class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile(r'^\s*summons?\s+(\S+)(?:\s+(.*?))?\s*^')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.ns = ns
        if dir is None:
            dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
        self.dir = dir
        self.help = 'summon <nick> [reason] - summon user'
        self.help += '\nlearn sms <nick> <email> - learn a nick\'s email'

    def response(self, **kwargs):
        nick, reason = kwargs['args']
        return '%s: not implemented (got: nick=%s, reason=%s)' % (
                kwargs['nick'], nick, reason)

if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=sys.argv[1:])
    sys.exit(0)
