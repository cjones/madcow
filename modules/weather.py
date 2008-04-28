#!/usr/bin/env python

"""Get weather report"""

import sys
import re
import os
from include.utils import UserAgent, stripHTML, Base
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
from include import rssparser
from learn import Main as Learn

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['Weather', 'Main']
__usage__ = 'set location <nick> <location>'

class Weather(Base):
    _base_url = 'http://www.wunderground.com/'
    _search_url = urljoin(_base_url, '/cgi-bin/findweather/getForecast')
    _rss_link = {'type': 'application/rss+xml'}
    _tempF = re.compile('(-?[0-9.]+)\s*\xb0\s*F', re.I)
    _bar = re.compile(r'\s*\|\s*')
    _keyval = re.compile(r'^\s*(.*?)\s*:\s*(.*?)\s*$')

    def __init__(self):
        self.ua = UserAgent()

    def forecast(self, location):
        page = self.ua.fetch(url=Weather._search_url, opts={'query': location},
                referer=Weather._base_url, method='GET')
        soup = BeautifulSoup(page)

        # disambiguation page
        if 'Search Results' in str(soup):
            table = soup.find('table', attrs={'class': 'boxB full'})
            rows = table.findAll('tr')
            results = []
            match = None
            for row in rows:
                cells = row.findAll('td', attrs={'class': 'sortC'})
                for cell in cells:
                    link = cell.find('a')
                    if link is None or 'addfav' in str(link['href']):
                        continue
                    city = str(link.contents[0])
                    href = urljoin(Weather._base_url, str(link['href']))
                    results.append(city)
                    if city.lower() == location.lower():
                        match = urljoin(Weather._base_url, href)
                        break
                if match:
                    break
            if match:
                page = self.ua.fetch(url=match)
                soup = BeautifulSoup(page)
            else:
                return 'Multiple results found: %s' % ', '.join(results)

        rss_url = soup.find('link', attrs=Weather._rss_link)['href']
        rss = rssparser.parse(rss_url)
        title = str(soup.find('h1').string).strip()
        conditions = stripHTML(rss['items'][0]['description'])
        fields = Weather._bar.split(conditions)
        data = {}
        for field in fields:
            try:
                key, val = Weather._keyval.search(field).groups()
                data[key] = val
            except:
                pass

        try:
            temp = float(Weather._tempF.search(data['Temperature']).group(1))
            if temp < 0:
                color = 6
            elif temp >=0 and temp <= 40:
                color = 2
            elif temp >= 40 and temp <= 60:
                color = 10
            elif temp >= 60 and temp <= 80:
                color = 3
            elif temp >= 80 and temp <= 100:
                color = 7
            elif temp > 100:
                color = 5
            data['Temperature'] = '\x03%s\x16\x16%s\x0F' % (color,
                    data['Temperature'])

        except:
            pass

        output = []
        for key, val in data.items():
            line = '%s: %s' % (key, val)
            output.append(line)

        output = ' | '.join(output)

        return '%s: %s' % (title, output)


class Main(Base):
    enabled = True
    pattern = re.compile('^\s*(?:fc|forecast|weather)(?:\s+(.*)$)?')
    require_addressing = True

    def __init__(self, madcow=None):
        self.weather = Weather()
        try:
            self.learn = Learn(ns=madcow.ns, dir=madcow.dir)
        except:
            self.learn = None

    def response(self, **kwargs):
        nick = kwargs['nick']

        try:
            args = kwargs['args'][0]
        except:
            args = None

        if args is None or args == '' and self.learn:
            query = self.learn.lookup('location', nick)
        elif args.startswith('@') and self.learn:
            query = self.learn.lookup('location', args[1:])
        else:
            query = args

        if query is None or query == '':
            return '%s: unknown nick. %s' % (nick, __usage__)

        try:
            return '%s: %s' % (nick, self.weather.forecast(query))
        except Exception, e:
            return "Couldn't find that place, maybe a bomb dropped on it"


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
