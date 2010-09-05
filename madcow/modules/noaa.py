"""
Alternative to wunderground that has more accurate data,
but only works within the united states.
"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.color import ColorLib
from learn import Main as Learn

class Main(Module):

    pattern = re.compile(r'^\s*noaa(?:\s+(@?)(.+?))?\s*$', re.I)
    help = 'noaa [location|@nick] - alternative weather (us only)'
    noaa_url = 'http://www.weather.gov/'
    noaa_search = 'http://forecast.weather.gov/zipcity.php'
    error = 'Something bad happened'

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
