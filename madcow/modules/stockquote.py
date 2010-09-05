"""Get stock quote from yahoo ticker"""

from madcow.util import Module, strip_html
from madcow.util.http import geturl
from urllib import quote
from madcow.util.color import ColorLib
import locale
import csv
import re

class UnknownSymbol(Exception):
    """Unknown Symbol Exception"""
    def __init__(self, symbolname):
        super(UnknownSymbol, self).__init__()
        self.symbolname = symbolname


class Yahoo(object):
    # query parameters are s: symbol n: name p: prev. close l: last trade with time (15 minute delay)
    # a mostly-accurate listing of possible parameters is available here: http://www.gummy-stuff.org/Yahoo-data.htm
    _quote_url = u'http://download.finance.yahoo.com/d/quotes.csv?s=SYMBOL&f=snpl&e=.csv'

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def get_quote(self, symbols):
        """Looks up the symbol from finance.yahoo.com, returns formatted result"""
        symbols = [quote(symbol) for symbol in symbols.split()]
        url = Yahoo._quote_url.replace(u'SYMBOL', "+".join(symbols))
        page = geturl(url)

        results = []
        for line in page.splitlines():
            data = csv.reader([line]).next()
            symbol = data[0]
            name = data[1]
            trade_time, last_trade = strip_html(data[3]).split(" - ")
            last_trade = locale.atof(last_trade)
            try:
                last_close = locale.atof(data[2])
                exchange = False
            except ValueError:
                last_close = last_trade
                exchange = True

            if trade_time == "N/A":
                trade_time = u'market close'

            if exchange:
                results.append(u'%s (%s) - %s: %.4f' % (name, symbol, trade_time, last_trade))
            else:
                delta = last_trade - last_close
                delta_perc = delta * 100.0 / last_close
                if delta < 0:
                    color = u'red'
                elif delta > 0:
                    color = u'green'
                else:
                    color = u'white'
                text = self.colorlib.get_color(color, text=u'%.2f (%+.2f %+.2f%%)' % (last_trade, delta, delta_perc))
                results.append(u'%s (%s) - Open: %.2f | %s: %s' % (name, symbol, last_close, trade_time, text))


        return u'\n'.join(results)


class Main(Module):
    pattern = re.compile(u'^\s*(?:stocks?|quote)\s+([ .=a-zA-Z0-9^]+)', re.I)
    require_addressing = True
    help = u'quote <symbol> - get latest stock quote'

    def init(self):
        self.colorlib = self.madcow.colorlib

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            response = unicode(self.yahoo.get_quote(query))
        except UnknownSymbol, error:
            response = u"Symbol %s not found, market may have crashed" % error.symbolname
        return response
