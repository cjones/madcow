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
import anydbm
import time
import os
from include.utils import Module
import logging as log

class Main(Module):

    pattern = Module._any
    priority = 1
    terminate = False
    allow_threading = False
    require_addressing = False
    help = 'seen <nick> - query bot about last time someone was seen speaking'
    seen = re.compile('^\s*seen\s+(\S+)\s*$', re.I)

    def __init__(self, madcow):
        self.dbfile = os.path.join(madcow.prefix,
                'data/db-%s-seen' % madcow.namespace)

    def dbm(self):
        return anydbm.open(self.dbfile, 'c', 0640)

    def get(self, user):
        user = user.lower()
        db = self.dbm()
        try:
            packed = db[user]
            db.close()
            channel, last, message = packed.split('/', 2)

            seconds = int(time.time() - float(last))
            last = '%s second%s' % (seconds, 's' * (seconds != 1))

            minutes = seconds / 60
            seconds = seconds % 60
            if minutes: last = '%s minute%s' % (minutes, 's' * (minutes != 1))

            hours = minutes / 60
            minutes = minutes % 60
            if hours: last = '%s hour%s' % (hours, 's' * (hours != 1))

            days = hours / 24
            hours = hours % 24
            if days: last = '%s day%s' % (days, 's' * (days != 1))

            return message, channel, last
        except:
            return None, None, None

    def set(self, nick, channel, message):
        packed = '%s/%s/%s' % (channel, time.time(), message)
        db = self.dbm()
        db[nick.lower()] = packed
        db.close()

    def response(self, nick, args, kwargs):
        channel = kwargs['channel']
        line = args[0]

        try:
            self.set(nick, channel, line)
            match = self.seen.search(line)
            if not match:
                return
            user = match.group(1)
            message, channel, last = self.get(user)
            if not message:
                return "%s: I haven't seen %s say anything plz" % (nick, user)
            return '%s: %s was last seen %s ago on %s saying "%s"' % (nick,
                    user, last, channel, message)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
