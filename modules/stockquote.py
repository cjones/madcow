#!/usr/bin/env python

"""Get stock quote from yahoo ticker"""

import sys
import re
import os
from include.utils import Base, UserAgent, stripHTML
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
import random

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
_namespace = 'madcow'
_dir = '..'

class Yahoo(Base):
    _quote_url = 'http://finance.yahoo.com/q?s=SYMBOL'
    _isfloat = re.compile(r'^\s*-?\s*[0-9.,]+\s*$')
    _green = '\x039'
    _red = '\x035'
    _reset = '\x0F'

    def __init__(self):
        self.ua = UserAgent()

    def get_quote(self, symbol):
        url = Yahoo._quote_url.replace('SYMBOL', symbol)
        page = self.ua.fetch(url)
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
                img = val.find('img')
                alt = str(img['alt'])
                val = alt + stripHTML(str(val.contents[0]))
            elif key == 'Ask:':
                continue
            else:
                val = stripHTML(str(val.contents[0]))

            if Yahoo._isfloat.search(val):
                val = val.replace(',', '')
                val = float(val)

            data[key] = val

            if key == 'Last Trade:' or key == 'Index Value:':
                current_value = val

            elif key == 'Open:':
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
                data['Change:'] = self._green + data['Change:'] + self._reset
            elif 'Down' in data['Change:']:
                data['Change:'] = self._red + data['Change:'] + self._reset
        except:
            pass

        # build friendly output
        output = []
        for key, val in data.items():
            if isinstance(val, float):
                val = '%.2f' % val
            output.append('%s %s' % (key, val))

        return '%s - ' % company + ', '.join(output)


class MatchObject(Base):

    def __init__(self, config=None, ns=_namespace, dir=_dir):
        self.config = config
        self.ns = ns
        self.dir = dir
        self.enabled = True
        self.pattern = re.compile('^\s*(?:stocks?|quote)\s+(\S+)', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'quote <symbol> - get latest stock quote'
        self.yahoo = Yahoo()

    def response(self, **kwargs):
        nick = kwargs['nick']
        query = kwargs['args'][0]

        try:
            return self.yahoo.get_quote(query)
        except Exception, e:
            return "Symbol not found, market may have crashed"


if __name__ == '__main__':
    mo = MatchObject()
    nick = os.environ['USER']
    args = ' '.join(sys.argv[1:])
    print mo.response(nick=nick, args=[args])
    sys.exit(0)
