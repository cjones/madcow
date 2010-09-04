#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Module to handle learning"""

import re
from include.utils import Module
import logging as log

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
        self.charset = madcow.charset
        self.prefix = madcow.prefix
        self.namespace = madcow.namespace

    def dbfile(self, db):
        dbfile = u'%s/data/db-%s-%s' % (self.prefix, self.namespace, db)
        return dbfile

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
            key = key.lower().encode(self.charset, 'replace')
            if dbm.has_key(key):
                return dbm[key].decode(self.charset, 'replace')
        finally:
            dbm.close()

    def set(self, db, key, val):
        dbm = self.dbm(db)
        try:
            key = key.lower().encode(self.charset, 'replace')
            val = val.encode(self.charset, 'replace')
            dbm[key] = val
        finally:
            dbm.close()

    def response(self, nick, args, kwargs):
        try:
            db, key, val = args
            if db not in self._allowed:
                return u'%s: unknown database' % nick
            self.set(db, key, val)
            return u'%s: set %s\'s %s to %s' % (nick, key, db, val)
        except Exception, error:
            log.warn(u'error in %s: %s' % (self.__module__, error))
            log.exception(error)
            return u"%s: couldn't set that" % nick
