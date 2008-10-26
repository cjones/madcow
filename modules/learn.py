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
        self.prefix = madcow.prefix
        self.namespace = madcow.namespace

    def dbfile(self, db):
        dbfile = '%s/data/db-%s-%s' % (self.prefix, self.namespace, db)
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

    def response(self, nick, args, kwargs):
        try:
            db, key, val = args
            if db not in self._allowed:
                return '%s: unknown database' % nick
            self.set(db, key, val)
            return '%s: set %s\'s %s to %s' % (nick, key, db, val)
        except Exception, error:
            log.warn('error in %s: %s' % (self.__module__, error))
            log.exception(error)
            return "%s: couldn't set that" % nick
