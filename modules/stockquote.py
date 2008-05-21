#!/usr/bin/env python

"""Get stock quote from yahoo ticker"""

import re
from include.utils import Base, Module, stripHTML
from include.useragent import geturl
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
import random

__version__ = '0.3'
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

        return '%s - ' % company + ' | '.join(output)


class Main(Module):
    pattern = re.compile('^\s*(?:stocks?|quote)\s+(\S+)', re.I)
    require_addressing = True
    help = 'quote <symbol> - get latest stock quote'

    def __init__(self, madcow=None):
        self.yahoo = Yahoo()

    def response(self, nick, args, **kwargs):
        query = args[0]
        try:
            return self.yahoo.get_quote(query)
        except Exception, e:
            return "Symbol not found, market may have crashed"


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    import os, sys
    sys.exit(main())
