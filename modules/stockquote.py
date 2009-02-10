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

__version__ = u'0.3'
__author__ = u'cj_ <cjones@gruntle.org>'

_namespace = u'madcow'
_dir = u'..'

class UnknownSymbol(Exception):

    pass


class Yahoo(object):

    _quote_url = u'http://finance.yahoo.com/q?s=SYMBOL'
    _isfloat = re.compile(r'^\s*-?\s*[0-9.,]+\s*$')

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def get_quote(self, symbol):
        url = Yahoo._quote_url.replace(u'SYMBOL', symbol)
        page = geturl(url)
        soup = BeautifulSoup(page)
        company = u' '.join([unicode(item)
                             for item in soup.find(u'h1').contents])
        company = stripHTML(company)
        tables = soup.findAll(u'table')
        if not tables:
            raise UnknownSymbol
        table = tables[0]
        rows = table.findAll(u'tr')
        data = {}
        current_price = 0.0
        last_price = 0.0

        # Yahoo emits numbers in the US format of course..
        locale.setlocale(locale.LC_NUMERIC, "en_US.UTF-8")
        for row in rows:
            key = row.findAll(u'th')[0]
            val = row.findAll(u'td')[0]
            key = unicode(key.contents[0])

            if key in (u'Last Trade:', u'Index Value:', u'Net Asset Value:'):
                current_price = locale.atof(stripHTML(unicode(val)))
            elif key == u'Prev Close:':
                last_price = locale.atof(stripHTML(unicode(val)))

        # calculate change
        delta = current_price - last_price
        delta_perc = 100 * delta / last_price

        otext = u"Open: %.2f" % last_price
        ptext = u"%.2f (%+.2f %+.2f%%)" % (current_price, delta, delta_perc)
        if delta > 0:
            ptext = self.colorlib.get_color(u'green', text=ptext)
        elif delta < 0:
            ptext = self.colorlib.get_color(u'red', text=ptext)
        ptext = u"Current: " + ptext

        data = [otext, ptext]

        # grab after hours data if it's available
        quotepara = soup.findAll(u'p')[1]
        if u"After Hours:" in quotepara.contents[0]:
            try:
                after_hours = float(quotepara.findAll(u'span')[0].contents[0])
                ah_delta = after_hours - current_price
                ah_delta_perc = ah_delta / current_price * 100
                ahtext = u'%.2f (%+.2f %+.2f%%)' % (
                        after_hours, ah_delta, ah_delta_perc)
                if ah_delta > 0:
                    ahtext = self.colorlib.get_color(u'green', text=ahtext)
                elif ah_delta < 0:
                    ahtext = self.colorlib.get_color(u'red', text=ahtext)
                ahtext = u"After Hours: " + ahtext
                data.append(ahtext)
            except ValueError:
                pass

        return u'%s - ' % company + u' | '.join(data)


class Main(Module):

    pattern = re.compile(u'^\s*(?:stocks?|quote)\s+(\S+)', re.I)
    require_addressing = True
    help = u'quote <symbol> - get latest stock quote'

    def __init__(self, madcow=None):
        if madcow is not None:
            colorlib = madcow.colorlib
        else:
            colorlib = ColorLib(u'ansi')
        self.yahoo = Yahoo(colorlib)

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            response = unicode(self.yahoo.get_quote(query))
        except UnknownSymbol:
            response = u"Symbol not found, market may have crashed"
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            response = u'%s: %s' % (nick, error)
        return response


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
