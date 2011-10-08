"""Module to handle learning"""

import re
from madcow.util import Module
from madcow.util.text import *
import os

try:
    import dbm
except ImportError:
    import anydbm as dbm

class Main(Module):

    pattern = re.compile(u'^\s*set\s+(\S+)\s+(\S+)\s+(.+)$', re.I)
    require_addressing = True
    allow_threading = False
    help = u'set <location|email> <nick> <val> - set db attribs'
    _allowed = [u'location', u'email', u'karma']

    def __init__(self, madcow=None):
        self.prefix = madcow.base

    def dbfile(self, db):
        return os.path.join(self.prefix, 'db', db)

    def dbm(self, db):
        dbfile = self.dbfile(db)
        return dbm.open(dbfile, u'c', 0640)

    def get_db(self, db):
        dbm = self.dbm(db)
        try:
            return dict(dbm)
        finally:
            dbm.close()

    def lookup(self, db, key):
        dbm = self.dbm(db)
        try:
            key = encode(key.lower())
            if dbm.has_key(key):
                return decode(dbm[key])
        finally:
            dbm.close()

    def set(self, db, key, val):
        dbm = self.dbm(db)
        try:
            key = encode(key.lower())
            val = encode(val)
            dbm[key] = val
        finally:
            dbm.close()

    def response(self, nick, args, kwargs):
        db, key, val = args
        if db not in self._allowed:
            return u'%s: unknown database' % nick
        self.set(db, key, val)
        return u'%s: set %s\'s %s to %s' % (nick, key, db, val)
