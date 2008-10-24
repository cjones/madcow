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
import locale

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
        current_price = 0.0
        last_price = 0.0
        locale.setlocale(locale.LC_NUMERIC, "en_US") # Yahoo emits numbers in the US format of course..
        for row in rows:
            key, val = row.findAll('td')
            key = str(key.contents[0])
            
            if key in ('Last Trade:', 'Index Value:'):
                current_price = locale.atof(stripHTML(str(val)))
            elif key == 'Prev Close:':
                last_price = locale.atof(stripHTML(str(val)))
        
        # calculate change
        delta = current_price - last_price
        delta_perc = 100 * delta / last_price
        
        otext = "Open: %.2f" % last_price
        ptext = "%.2f (%+.2f %+.2f%%)" % (current_price, delta, delta_perc)
        if delta > 0:
            ptext = self.colorlib.get_color('green', text=ptext)
        elif delta < 0:
            ptext = self.colorlib.get_color('red', text=ptext)
        ptext = "Current: " + ptext
        
        data = [otext, ptext]
        
        # grab after hours data if it's available
        quotepara = soup.findAll('p')[1]
        if "After Hours:" in quotepara.contents[0]:
            try:
                after_hours = float(quotepara.findAll('span')[0].contents[0])
                ah_delta = after_hours - current_price
                ah_delta_perc = ah_delta / current_price * 100
                ahtext = '%.2f (%+.2f %+.2f%%)' % (after_hours, ah_delta, ah_delta_perc)
                if ah_delta > 0:
                    ahtext = self.colorlib.get_color('green', text=ahtext)
                elif ah_delta < 0:
                    ahtext = self.colorlib.get_color('red', text=ahtext)
                ahtext = "After Hours: " + ahtext
                data.append(ahtext)
            except ValueError:
                pass

        return '%s - ' % company + ' | '.join(data)


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
