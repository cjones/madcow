#!/usr/bin/env python

"""
Module to handle learning
"""

import sys
import re
import anydbm
import os

__allowed__ = ['location', 'email', 'karma']

class MatchObject(object):
    pattern = re.compile('^\s*set\s+(\S+)\s+(\S+)\s+(.+)$', re.I)

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = MatchObject.pattern
        self.requireAddressing = True
        self.thread = False
        self.wrap = False
        if dir is None:
            dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
        self.dir = dir
        self.ns = ns
        self.help = 'set <location|email> <nick> <val> - set db attribs'

    def dbfile(self, db):
        dbfile = '%s/data/db-%s-%s' % (self.dir, self.ns, db)
        return dbfile

    def dbm(self, db):
        dbfile = self.dbfile(db)
        return anydbm.open(dbfile, 'c', 0640)

    def get_db(self, db):
        dbm = self.dbm(db)
        db = {}
        for key in dbm.keys():
            db[key] = dbm[key]
        dbm.close()
        return db

    def lookup(self, db, key):
        dbm = self.dbm(db)
        try:
            val = dbm[key.lower()]
        except:
            val = None
        dbm.close()
        return val

    def set(self, db, key, val):
        dbm = self.dbm(db)
        dbm[key.lower()] = val
        dbm.close()

    def response(self, **kwargs):
        nick = kwargs['nick']
        db, key, val = kwargs['args']
        if db not in __allowed__:
            return '%s: unknown database' % nick
        self.set(db, key, val)
        return '%s: set %s\'s %s to %s' % (nick, key, db, val)

if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=sys.argv[1:])
    sys.exit(0)
