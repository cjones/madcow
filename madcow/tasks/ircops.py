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

"""Periodically checks for people that need to be opped"""

from time import time as unix_time, sleep
import logging as log

class Main(object):

    priority = 0
    enabled = True

    def __init__(self, madcow):
        self.madcow = madcow
        self.enabled = madcow.config.ircops.enabled
        self.frequency = madcow.config.ircops.updatefreq
        self.output = None
        if madcow.config.main.module != u'irc':
            self.enabled = False

    def response(self, *args):
        # determine who can be opped
        auto_op = []
        passwd = self.madcow.admin.authlib.get_passwd()
        for nick, data in passwd.items():
            if u'o' in data[u'flags']:
                auto_op.append(nick.lower())

        # issue NAMES update and wait for it to refresh (handled in irc.py)
        self.madcow.server.names(self.madcow.channels)
        while True:
            now = unix_time()
            delta = now - self.madcow.last_names_update
            if delta < self.frequency:
                break
            if delta >= (self.frequency * 2 -1):
                return
            sleep(.25)

        for channel, names in self.madcow.names.items():
            nicks = [nick for nick, opped in names.items() if not opped]
            if self.madcow.server.get_nickname() in nicks:
                log.warn(u'cannot give ops until i get it myself')
                return
            nicks = [nick for nick in nicks if nick in auto_op]
            for i in range(0, len(nicks), 6):
                line = nicks[i:i+6]
                log.info(u'opping on %s to %s' % (channel, u' '.join(line)))
                line = u'+' + (u'o' * len(line)) + u' ' + u' '.join(line)
                self.madcow.server.mode(channel, line)
