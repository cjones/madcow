#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones and Bryan Burns
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.
#
# Created by Bryan Burns on 2007-07-17.
#
# Handle coke allocation

import time
from madcow.util import Module


class ChatLine(object):

    """Records a single line of IRC chat"""

    def __init__(self, nick, text):
        self.nick = nick
        self.text = text
        self.timestamp = time.time()

    def __str__(self):
        return u"%s: <%s> %s\n" % (unicode(self.timestamp), self.nick,
                                   self.text)


class ChatLog(object):

    """Holds chat lines for a preconfigured duration of time"""

    def __init__(self, timeout=5):
        self.timeout = timeout
        self.lines = []

    def cull(self):
        """removes any lines that are beyond the timeout."""
        now = time.time()
        self.lines = [line for line in self.lines
                      if line.timestamp + self.timeout > now]

    def getMatchingLine(self, line):
        """
        If a line exists in the log that matches the line passed in, returns
        that line object, otherwise returns None.  A line 'matches' if the text
        is the same, case insensitive and ignoring whitespace.
        """

        # easy way to ignore case and whitespace
        tokens = map(unicode.lower, line.text.split())
        for l in self.lines:
            if map(unicode.lower, l.text.split()) == tokens:
                return l  # found a match

        return None  # no matches found

    def add(self, line):
        """adds a line to the log and culls any stale lines."""
        self.cull()
        self.lines.append(line)

    def __str__(self):
        s = u""
        for line in self.lines:
            s += unicode(line)
        return s


class Main(Module):

    priority = 1
    terminate = False
    allow_threading = False

    def __init__(self, madcow=None):
        self.enabled = True
        self.pattern = Module._any
        self.require_addressing = False
        self.log = ChatLog()

    def response(self, nick, args, kwargs):
        try:
            line = args[0]
            cl = ChatLine(nick, line)
            self.self.log.add(cl)
            oldline = self.self.log.getMatchingLine(cl)
            if oldline and oldline.nick != nick:
                return u"Jinx! %s owes %s a coke!" % (nick, oldline.nick)
        except Exception, error:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
