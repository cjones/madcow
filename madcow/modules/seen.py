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

"""Keep track of what people last said"""

import re
import time
import os
from madcow.util import Module


try:
    import dbm
except ImportError:
    import anydbm as dbm

class Main(Module):

    pattern = Module._any
    priority = 1
    terminate = False
    allow_threading = False
    require_addressing = False
    help = u'seen <nick> - query bot about last time someone was seen speaking'
    seen = re.compile(u'^\s*seen\s+(\S+)\s*$', re.I)

    def __init__(self, madcow):
        self.charset = madcow.charset
        self.dbfile = os.path.join(madcow.base, 'db', 'seen')

    def dbm(self):
        return dbm.open(self.dbfile, u'c', 0640)

    def get(self, user):
        db = self.dbm()
        try:
            user = user.lower().encode(self.charset, 'replace')
            packed = db[user]
            packed = packed.decode(self.charset, 'replace')
            channel, last, message = packed.split(u'/', 2)

            seconds = int(time.time() - float(last))
            last = u'%s second%s' % (seconds, u's' * (seconds != 1))

            minutes = seconds / 60
            seconds = seconds % 60
            if minutes:
                last = u'%s minute%s' % (minutes, u's' * (minutes != 1))

            hours = minutes / 60
            minutes = minutes % 60
            if hours:
                last = u'%s hour%s' % (hours, u's' * (hours != 1))

            days = hours / 24
            hours = hours % 24
            if days:
                last = u'%s day%s' % (days, u's' * (days != 1))

            return message, channel, last
        except:
            return None, None, None
        finally:
            db.close()

    def set(self, nick, channel, message):
        packed = u'%s/%s/%s' % (channel, time.time(), message)
        db = self.dbm()
        try:
            nick = nick.lower().encode(self.charset, 'replace')
            packed = packed.encode(self.charset, 'replace')
            db[nick] = packed
        finally:
            db.close()

    def response(self, nick, args, kwargs):
        channel = kwargs[u'channel']
        line = args[0]

        try:
            self.set(nick, channel, line)
            match = self.seen.search(line)
            if not match:
                return
            user = match.group(1)
            message, channel, last = self.get(user)
            if not message:
                return u"%s: I haven't seen %s say anything plz" % (nick, user)
            return u'%s: %s was last seen %s ago on %s saying "%s"' % (
                    nick, user, last, channel, message)
        except Exception, error:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
