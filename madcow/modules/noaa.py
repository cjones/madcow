"""
Alternative to wunderground that has more accurate data,
but only works within the united states.
"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.color import ColorLib
from madcow.util.text import *
from learn import Main as Learn

class Main(Module):

    pattern = re.compile(r'^\s*noaa(?:\s+(@?)(.+?))?\s*$', re.I)
    help = 'noaa [location|@nick] - alternative weather (us only)'
    noaa_url = 'http://www.weather.gov/'
    noaa_search = 'http://forecast.weather.gov/zipcity.php'
    error = 'Something bad happened'
    fc_re = re.compile(r'^myforecast-current')

    def init(self):
        self.colorlib = self.madcow.colorlib
        try:
            self.learn = Learn(madcow=self.madcow)
        except:
            self.learn = None

    def response(self, nick, args, kwargs):
        if not args[1]:
            args = 1, nick
        if args[0]:
            location = self.learn.lookup('location', args[1])
            if not location:
                return u'%s: Try: set location <nick> <location>' % nick
        else:
            location = args[1]
        response = self.getweather(location)
        if not response:
            response = self.error
        return u'%s: %s' % (nick, response)

    def getweather(self, location):
        """Look up NOAA weather"""
        soup = getsoup(self.noaa_search, {'inputstring': location}, referer=self.noaa_url)
        return u' / '.join(map(self.render, soup.findAll(attrs={'class': self.fc_re})))

    @staticmethod
    def render(node):
        data = strip_html(decode(node.renderContents(), 'utf-8'))
        return data.strip()
