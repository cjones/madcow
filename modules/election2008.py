#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Chris Jones
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

"""Predicted Electoral Vote Count"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from include.colorlib import ColorLib

__version__ = u'0.1'
__author__ = u'Chris Jones <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*(election|ev)\s*$', re.I)
    help = u'ev - current election 2008 vote prediction'
    _baseurl = u'http://www.electoral-vote.com/'
    _score_re = re.compile(r'<td class="score">(.*?)</td>', re.DOTALL)
    _dem_re = re.compile(r'<span class="dem">(.*?)\s+(\d+)')
    _gop_re = re.compile(r'<span class="gop">(.*?)\s+(\d+)')
    _tie_re = re.compile(r'(Ties)\s+(\d+)')

    def __init__(self, madcow=None):
        if madcow is not None:
            self.colorlib = madcow.colorlib
        else:
            self.colorlib = ColorLib(u'ansi')

    def colorize(self, color, key, val):
        key = self.colorlib.get_color(color, text=key)
        return u'%s: %s' % (key, val)

    def response(self, nick, args, kwargs):
        try:
            page = geturl(self._baseurl)
            try:
                score = self._score_re.search(page).group(1)
                dem = self._dem_re.search(score).groups()
                gop = self._gop_re.search(score).groups()
                # XXX diebold patch :D
                #dem, gop = (dem[0], gop[1]), (gop[0], dem[1])
                tie = None
                try:
                    tie = self._tie_re.search(score).groups()
                except AttributeError:
                    pass
            except AttributeError:
                raise Exception(u"couldn't parse page")
            output = [self.colorize(u'blue', *dem), self.colorize(u'red', *gop)]
            if tie:
                output.append(self.colorize(u'white', *tie))
            return u'%s: %s' % (nick, u', '.join(output))
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
