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

"""Infobot style karma"""

from madcow.util import Module
import re
from learn import Main as Learn
import logging as log

__version__ = u'0.1'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = [u'Karma', u'Main']

class KarmaResponse(object):

    def __init__(self, reply, matched):
        self.reply = reply
        self.matched = matched


class Karma(object):

    """Infobot style karma"""

    _adjust_pattern = re.compile(r'^\s*(.*?)[+-]([+-]+)\s*$')
    _query_pattern = re.compile(r'^\s*karma\s+(\S+)\s*\?*\s*$')
    _dbname = u'karma'

    def __init__(self, madcow):
        self.learn = Learn(madcow)

    def process(self, nick, input):
        kr = KarmaResponse(reply=None, matched=False)

        # see if someone is trying to adjust karma
        try:
            target, adjustment = Karma._adjust_pattern.search(input).groups()
            # don't let people adjust their own karma ;p
            if nick.lower() != target.lower():
                self.adjust(nick=target, adjustment=adjustment)
            kr.matched = True
        except AttributeError:
            pass

        # detect a query for someone's karma
        try:
            target = Karma._query_pattern.search(input).group(1)
            karma = self.query(nick=target)
            kr.matched = True
            kr.reply = u"%s: %s's karma is %s" % (nick, target, karma)
        except AttributeError:
            pass
        return kr

    def set(self, nick, karma):
        self.learn.set(Karma._dbname, nick.lower(), unicode(karma))

    def adjust(self, nick, adjustment):
        karma = self.query(nick)
        adjustment, size = adjustment[0], len(adjustment)
        exec(u'karma ' + adjustment + u'= size')
        self.set(nick=nick, karma=karma)

    def query(self, nick):
        karma = self.learn.lookup(Karma._dbname, nick.lower())
        if karma is None:
            karma = 0
            self.set(nick=nick, karma=karma)
        return int(karma)


class Main(Module):

    """This object is autoloaded by the bot"""

    pattern = Module._any
    require_addressing = False
    help = u"<nick>[++/--] - adjust someone's karma"
    allow_threading = False

    def __init__(self, madcow=None):
        self.karma = Karma(madcow)

    def response(self, nick, args, kwargs):
        """This function should return a response to the query or None."""
        input = args[0]
        try:
            kr = self.karma.process(nick, input)
            kwargs[u'req'].matched = kr.matched
            if kr.reply:
                return unicode(kr.reply)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: problem with command: %s' % (nick, error)
