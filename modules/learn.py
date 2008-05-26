#!/usr/bin/env python

"""Module to handle learning"""

import re
import anydbm
from include.utils import Module
import logging as log

class Main(Module):
    pattern = re.compile('^\s*set\s+(\S+)\s+(\S+)\s+(.+)$', re.I)
    require_addressing = True
    allow_threading = False
    help = 'set <location|email> <nick> <val> - set db attribs'
    _allowed = ['location', 'email', 'karma']

    def __init__(self, madcow=None):
        self.dir = madcow.dir
        self.ns = madcow.ns

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

    def response(self, nick, args, **kwargs):
        try:
            db, key, val = args
            if db not in self._allowed:
                return '%s: unknown database' % nick
            self.set(db, key, val)
            return '%s: set %s\'s %s to %s' % (nick, key, db, val)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: couldn't set that" % nick

