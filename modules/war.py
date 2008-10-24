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
from include import rssparser
from include.utils import Module, stripHTML
from include.useragent import geturl
from include.BeautifulSoup import BeautifulSoup
import logging as log
from include.colorlib import ColorLib

__version__ = '0.3'
__author__ = 'cj_ <cjones@gruntle.org>'
__all__ = []

FORMAT = 'Terror: %s, DoomsDay: %s, IranWar: %s, IraqWar: %s, BodyCount: %s'

class Terror(object):
    _url = 'http://www.dhs.gov/dhspublic/getAdvisoryCondition'
    _re_level = re.compile(r'<THREAT_ADVISORY CONDITION="(\w+)" />')
    _color_map = {
        'severe': 'red',
        'high': 'orange',
        'elevated': 'bright yellow',
        'guarded': 'bright blue',
        'low': 'bright green',
    }

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def level(self):
        try:
            doc = geturl(Terror._url)
            level = self._re_level.search(doc).group(1)
            color = self._color_map[level.lower()]
            return self.colorlib.get_color(color, text=level)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return 'UNKNOWN'


class DoomsDay(object):
    _url = 'http://www.thebulletin.org/'
    _re_time = re.compile(r'<div class="module-content"><h3>(.*?)</h3>')

    def time(self):
        try:
            doc = geturl(DoomsDay._url)
            time = DoomsDay._re_time.search(doc).group(1)
            return time
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return 'UNKNOWN'


class IranWar(object):
    _url = 'http://www.areweatwarwithiran.com/rss.xml'

    def war(self):
        try:
            rss = rssparser.parse(IranWar._url)
            return rss.entries[0].title.encode(rss.encoding)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return 'UNKNOWN'


class IraqWar(object):
    _war_url = 'http://areweatwarwithiraq.com/rss.xml'
    _bodycount_url = 'http://www.iraqbodycount.org/'
    _re_whitespace = re.compile(r'\s+')

    def war(self):
        try:
            rss = rssparser.parse(IraqWar._war_url)
            return rss.entries[0].title.encode(rss.encoding)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return 'UNKNOWN'

    def bodycount(self):
        try:
            doc = geturl(IraqWar._bodycount_url)
            soup = BeautifulSoup(doc)
            data = soup.find('td', attrs={'class': 'main-num'})
            data = data.find('a')
            data = str(data.contents[0])
            data = stripHTML(data)
            data = IraqWar._re_whitespace.sub(' ', data)
            data = data.strip()
            return data
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return 'UNKNOWN'


class Main(Module):
    pattern = re.compile('^\s*(?:terror|doomsday|war)\s*$', re.I)
    require_addressing = True
    help = 'terror - NEVAR FORGET'

    def __init__(self, madcow=None):
        if madcow is not None:
            colorlib = madcow.colorlib
        else:
            colorlib = ColorLib('ansi')
        self.terror = Terror(colorlib)
        self.doom = DoomsDay()
        self.iran = IranWar()
        self.iraq = IraqWar()

    def response(self, nick, args, kwargs):
        try:
            return FORMAT % (self.terror.level(), self.doom.time(),
                    self.iran.war(), self.iraq.war(), self.iraq.bodycount())
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: problem with query: %s' % (nick, e)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
