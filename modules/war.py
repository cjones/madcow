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

"""NEVAR FORGET"""

import re
from include import feedparser
from include.utils import Module, stripHTML
from include.useragent import geturl
import logging as log
from include.colorlib import ColorLib

__version__ = u'0.3'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = []

FORMAT = u'Terror: %s, DoomsDay: %s, IranWar: %s, IraqWar: %s, BodyCount: %s, WHO Pandemic: %s'

class WHO(object):

    """WHO pandemic phase"""

    phase_re = re.compile(r'The current WHO phase of pandemic alert is (\d+)', re.I)
    url = 'http://www.who.int/csr/disease/avian_influenza/phase/en/index.html'
    colors = {'1': 'bright green',
              '2': 'bright cyan',
              '3': 'bright blue',
              '4': 'bright yellow',
              '5': 'orange',
              '6': 'red'}

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def phase(self):
        try:
            doc = geturl(self.url)
            phase = self.phase_re.search(doc).group(1)
            color = self.colors[phase]
            return self.colorlib.get_color(color, text=phase)
        except Exception, error:
            log.warn(error)
            return 'UNKNOWN'


class Terror(object):

    _url = u'http://www.dhs.gov/dhspublic/getAdvisoryCondition'
    _re_level = re.compile(r'<THREAT_ADVISORY CONDITION="(\w+)" />')
    _color_map = {u'severe': u'red',
                  u'high': u'orange',
                  u'elevated': u'bright yellow',
                  u'guarded': u'bright blue',
                  u'low': u'bright green'}

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def level(self):
        try:
            doc = geturl(Terror._url)
            level = self._re_level.search(doc).group(1)
            color = self._color_map[level.lower()]
            return self.colorlib.get_color(color, text=level)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'UNKNOWN'


class DoomsDay(object):

    _url = u'http://www.thebulletin.org/'
    _re_time = re.compile(r'<div class="module-content"><h3>(.*?)</h3>')

    def time(self):
        try:
            doc = geturl(DoomsDay._url)
            time = self._re_time.search(doc).group(1)
            return time
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'UNKNOWN'


class IranWar(object):

    _url = u'http://www.areweatwarwithiran.com/rss.xml'

    def war(self):
        try:
            rss = feedparser.parse(self._url)
            return rss.entries[0].title
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'UNKNOWN'


class IraqWar(object):

    _war_url = u'http://areweatwarwithiraq.com/rss.xml'
    _bodycount_url = u'http://www.iraqbodycount.org/database/'
    _re_whitespace = re.compile(r'\s+')
    _bodycount_re = re.compile(r"<p class='ibc-range'>(.*?)</p>", re.DOTALL)

    def war(self):
        try:
            rss = feedparser.parse(self._war_url)
            return rss.entries[0].title
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'UNKNOWN'

    def bodycount(self):

        try:
            doc = geturl(self._bodycount_url)
            data = self._bodycount_re.search(doc).group(1)
            data = data.decode('ascii', 'replace')
            data = stripHTML(data)
            data = self._re_whitespace.sub(u' ', data)
            data = data.strip()
            return data
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'UNKNOWN'


class Main(Module):

    pattern = re.compile(u'^\s*(?:terror|doomsday|war)\s*$', re.I)
    require_addressing = True
    help = u'terror - NEVAR FORGET'

    def __init__(self, madcow=None):
        if madcow is not None and hasattr(madcow, 'colorlib'):
            colorlib = madcow.colorlib
        else:
            colorlib = ColorLib(u'ansi')
        self.terror = Terror(colorlib)
        self.doom = DoomsDay()
        self.iran = IranWar()
        self.iraq = IraqWar()
        self.who = WHO(colorlib)

    def response(self, nick, args, kwargs):
        try:
            return FORMAT % (self.terror.level(), self.doom.time(),
                             self.iran.war(), self.iraq.war(),
                             self.iraq.bodycount(), self.who.phase())
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: problem with query: %s' % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
