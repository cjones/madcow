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

"""Get stock quote from yahoo ticker"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
import random
import logging as log
from include.colorlib import ColorLib

__version__ = '0.3'
__author__ = 'cj_ <cjones@gruntle.org>'

_namespace = 'madcow'
_dir = '..'

class Yahoo(object):
    _quote_url = 'http://finance.yahoo.com/q?s=SYMBOL'
    _isfloat = re.compile(r'^\s*-?\s*[0-9.,]+\s*$')

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def get_quote(self, symbol):
        url = Yahoo._quote_url.replace('SYMBOL', symbol)
        page = geturl(url)
        soup = BeautifulSoup(page)
        company = ' '.join([str(item) for item in soup.find('h1').contents])
        company = stripHTML(company)
        tables = soup.findAll('table')
        table = tables[0]
        rows = table.findAll('tr')
        data = {}
        current_value = 0.0
        open_value = 0.0
        for row in rows:
            key, val = row.findAll('td')
            key = str(key.contents[0])
            if key == 'Change:':
                try:
                    img = val.find('img')
                    alt = str(img['alt'])
                    val = alt + stripHTML(str(val.contents[0]))
                except:
                    val = '0.00%'
            elif key == 'Ask:':
                continue
            else:
                val = stripHTML(str(val.contents[0]))

            val = val.replace(',', '')
            if Yahoo._isfloat.search(val):
                val = float(val)

            data[key] = val

            if key == 'Last Trade:' or key == 'Index Value:':
                current_value = val

            elif key == 'Prev Close:':
                open_value = val

        # see if we can calculate percentage
        try:
            change = 100 * (current_value - open_value) / open_value
            data['Change:'] += ' (%.2f%%)' % change
        except:
            pass

        # try and colorize the change field
        try:
            if 'Up' in data['Change:']:
                data['Change:'] = self.colorlib.get_color('green',
                        text=data['Change:'])
            elif 'Down' in data['Change:']:
                data['Change:'] = self.colorlib.get_color('red',
                        text=data['Change:'])
        except:
            pass

        # build friendly output
        output = []
        for key, val in data.items():
            if isinstance(val, float):
                val = '%.2f' % val
            output.append('%s %s' % (key, val))

        return '%s - ' % company + ' | '.join(output)


class Main(Module):
    pattern = re.compile('^\s*(?:stocks?|quote)\s+(\S+)', re.I)
    require_addressing = True
    help = 'quote <symbol> - get latest stock quote'

    def __init__(self, madcow=None):
        if madcow is not None:
            colorlib = madcow.colorlib
        else:
            colorlib = ColorLib('ansi')
        self.yahoo = Yahoo(colorlib)

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            return self.yahoo.get_quote(query)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "Symbol not found, market may have crashed"


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
