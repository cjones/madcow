#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones
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

"""
Alternative to wunderground that has more accurate data,
but only works within the united states.
"""


import re

from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.color import ColorLib
from learn import Main as Learn

__version__ = '1.0'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*noaa(?:\s+(@?)(.+?))?\s*$', re.I)
    help = 'noaa [location|@nick] - alternative weather (us only)'

    noaa_url = 'http://www.weather.gov/'
    noaa_search = 'http://forecast.weather.gov/zipcity.php'

    def __init__(self, madcow=None):
        if madcow is not None:
            self.colorlib = madcow.colorlib
        else:
            self.colorlib = ColorLib('ansi')
        try:
            self.learn = Learn(madcow=madcow)
        except:
            self.learn = None
        super(Main, self).__init__(madcow)

    def response(self, nick, args, kwargs):
        try:
            if not args[1]:
                args = 1, nick
            if args[0]:
                location = self.learn.lookup('location', args[1])
                if not location:
                    return u'%s: Try: set location <nick> <location>' % nick
            else:
                location = args[1]
            response = self.getweather(location)
        except Exception, error:
            self.log.warn('error in module %s' % self.__module__)
            self.log.exception(error)
            response = u'Something bad happened'
        return u'%s: %s' % (nick, response)

    def getweather(self, location):
        """Look up NOAA weather"""
        soup = getsoup(self.noaa_search, {'inputstring': location},
                       referer=self.noaa_url)

        # jesus fucking christ, their html is bad.. looks like 1987
        # nested tables, font tags, and not a single class or id.. good game
        current = soup.find('img', alt='Current Local Weather')
        if not current:
            return u'NOAA website is having issues'
        current = current.findNext('table').table.table
        temp = current.td.font.renderContents().replace('<br />', '|')
        temp = strip_html(temp.decode('utf-8')).replace('\n', '').strip()
        cond, _, tempf, tempc = temp.split('|')
        tempc = tempc.replace('(', '').replace(')', '')
        tempf, tempc = self.docolor(tempf, tempc)
        other = current.table
        items = [u'%s (%s) - %s' % (tempf, tempc, cond)]
        for row in other('tr'):
            if row.a:
                continue
            cells = row('td')
            key = self.render(cells[0])
            val = self.render(cells[1])
            items.append(u'%s %s' % (key, val))
        return u', '.join(items)

    def docolor(self, tempf, tempc):
        temp = int(tempf.split(u'\xb0')[0])
        blink = False
        if temp < 0:
            color = 'magenta'
        elif temp >=0 and temp < 40:
            color = 'blue'
        elif temp >= 40 and temp < 60:
            color = 'cyan'
        elif temp >= 60 and temp < 80:
            color = 'green'
        elif temp >= 80 and temp < 90:
            color = 'yellow'
        elif temp >= 90 and temp < 100:
            color = 'red'
        elif temp >= 100:
            color = 'red'
            blink = True
        tempf = self.colorlib.get_color(color, text=tempf)
        tempc = self.colorlib.get_color(color, text=tempc)
        if blink:
            tempf = u'\x1b[5m' + tempf + u'\x1b[0m'
            tempc = u'\x1b[5m' + tempc + u'\x1b[0m'
        return tempf, tempc

    @staticmethod
    def render(node):
        data = strip_html(node.renderContents().decode('utf-8', 'ignore'))
        return data.strip()


if __name__ == '__main__':
    from madcow.util import test_module
    test_module(Main)
