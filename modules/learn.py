#!/usr/bin/env python

# Module to handle learning

import sys
import re
import anydbm
import os

# class for this module
class MatchObject(object):
    def __init__(self, config=None, ns='default', dir=None):
        self.enabled = True                # True/False - enabled?
        self.pattern = re.compile('^\s*learn\s+(\S+)\s+(.+)')    # regular expression that needs to be matched
        self.requireAddressing = True            # True/False - require addressing?
        self.thread = False                # True/False - should bot spawn thread?
        self.wrap = False                # True/False - wrap output?
        if dir is None: dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
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

    # function to generate a response
    def response(self, *args, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']
        if len(args) == 1:
            return self.lookup(args[0])
        else:
            self.set(args[0], args[1])
            return '%s: I learned that %s is in %s' % (nick, args[0], args[1])


# this is just here so we can test the module from the commandline
def main(argv = None):
    if argv is None: argv = sys.argv[1:]
    obj = MatchObject()
    print obj.response(nick='testUser', args=argv)

    return 0

if __name__ == '__main__': sys.exit(main())
