#!/usr/bin/env python

"""
Module to handle learning
"""

import sys
import re
import anydbm
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*learn\s+(\S+)\s+(.+)')
        self.requireAddressing = True
        self.thread = False
        self.wrap = False
        if dir is None:
            dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
        self.dbfile = dir + '/data/db-%s-locations' % ns

    def lookup(self, nick):
        db = anydbm.open(self.dbfile, 'c', 0640)
        try: location = db[nick.lower()]
        except: location = None
        db.close()
        return location

    def set(self, nick, location):
        db = anydbm.open(self.dbfile, 'c', 0640)
        db[nick.lower()] = location
        db.close()

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        if len(args) == 1:
            return self.lookup(args[0])
        else:
            self.set(args[0], args[1])
            return '%s: I learned that %s is in %s' % (nick, args[0], args[1])


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=sys.argv[1:])
    sys.exit(0)
