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

from include.utils import Module, stripHTML
from include.useragent import geturl
import logging as log
from include.colorlib import ColorLib
import locale
import csv

__version__ = u'0.4'
__author__ = u'cj_ <cjones@gruntle.org> / toast <toast@evilscheme.org>'

_namespace = u'madcow'
_dir = u'..'

class UnknownSymbol(Exception):
    pass


class Yahoo(object):
    # query parameters are s: symbol n: name p: prev. close k1: last trade (real time)
    # a mostly-accurate listing of possible parameters is available here: http://www.gummy-stuff.org/Yahoo-data.htm
    _quote_url = u'http://download.finance.yahoo.com/d/quotes.csv?s=SYMBOL&f=snpk1&e=.csv'
    
    def __init__(self, colorlib):
        self.colorlib = colorlib
    
    def get_quote(self, symbol):
        """Looks up the symbol from finance.yahoo.com, returns formatted result"""
        url = Yahoo._quote_url.replace(u'SYMBOL', symbol)
        page = geturl(url)
        
        data = csv.reader([page]).next()
        symbol = data[0]
        name = data[1]
        try:
            last_close = locale.atof(data[2])
        except ValueError:
            raise UnknownSymbol()
        trade_time, last_trade = stripHTML(data[3]).split(" - ")
        last_trade = locale.atof(last_trade)
        
        if trade_time == "N/A":
            trade_time = "market close"
        
        delta = last_trade - last_close
        delta_perc = delta * 100.0 / last_close
        
        if delta < 0:
            color = u'red'
        elif delta > 0:
            color = u'green'
        else:
            color = u'white'
        
        text = self.colorlib.get_color(color, text="%.2f (%+.2f %+.2f%%)" % (last_trade, delta, delta_perc))
        
        return "%s (%s) - Open: %.2f | %s: %s" % (name, symbol, last_close, trade_time, text)


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
