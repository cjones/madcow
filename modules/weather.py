#!/usr/bin/env python

"""Get weather report"""

import re
from include.utils import stripHTML, Module
from include.useragent import geturl
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
from include import rssparser
from learn import Main as Learn
import logging as log
from include.colorlib import ColorLib

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['Weather', 'Main']
__usage__ = 'set location <nick> <location>'

class Weather:
    baseurl = 'http://www.wunderground.com/'
    search = urljoin(baseurl, '/cgi-bin/findweather/getForecast')
    _rss_link = {'type': 'application/rss+xml'}
    _tempF = re.compile('(-?[0-9.]+)\s*\xb0\s*F', re.I)
    _bar = re.compile(r'\s*\|\s*')
    _keyval = re.compile(r'^\s*(.*?)\s*:\s*(.*?)\s*$')

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def forecast(self, location):
        page = geturl(url=self.search, opts={'query': location},
                referer=self.baseurl)
        soup = BeautifulSoup(page)

        # disambiguation page
        if 'Search Results' in str(soup):
            table = soup.find('table', attrs={'class': 'dataTable'})
            tbody = soup.find('tbody')
            results = [row.findAll('td')[0].find('a')
                       for row in tbody.findAll('tr')]
            results = [(normalize(str(result.contents[0])),
                        urljoin(Weather.baseurl, str(result['href'])))
                       for result in results]

            match = None
            for result in results:
                if result[0] == normalize(location):
                    match = result[1]
                    break
            if match is None:
                match = results[0][1]
            page = geturl(url=match, referer=self.search)
            soup = BeautifulSoup(page)

        rss_url = soup.find('link', attrs=self._rss_link)['href']
        rss = rssparser.parse(rss_url)
        title = str(soup.find('h1').string).strip()
        conditions = stripHTML(rss['items'][0]['description'])
        fields = self._bar.split(conditions)
        data = {}
        for field in fields:
            try:
                key, val = self._keyval.search(field).groups()
                data[key] = val
            except:
                pass

        try:
            temp = float(self._tempF.search(data['Temperature']).group(1))
            blink = False
            if temp < 0:
                color = 'magenta'
            elif temp >=0 and temp < 40:
                color = 'bue'
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
            data['Temperature'] = self.colorlib.get_color(color,
                    text=data['Temperature'])
            if blink:
                data['Temperature'] = '\x1b[5m' + data['Temperature'] + \
                        '\x1b[0m'

        except:
            pass

        output = []
        for key, val in data.items():
            line = '%s: %s' % (key, val)
            output.append(line)

        output = ' | '.join(output)

        return '%s: %s' % (title, output)


class Main(Module):
    pattern = re.compile('^\s*(?:fc|forecast|weather)(?:\s+(.*)$)?')
    require_addressing = True
    help = 'fc [location] - look up weather forecast'

    def __init__(self, madcow=None):
        if madcow is not None:
            colorlib = madcow.colorlib
        else:
            colorlib = ColorLib('ansi')
        self.weather = Weather(colorlib)
        try:
            self.learn = Learn(madcow=madcow)
        except:
            self.learn = None

    def response(self, nick, args, kwargs):

        try:
            args = args[0]
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
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "Couldn't find that place, maybe a bomb dropped on it"


whitespace = re.compile(r'\s+')
year = re.compile(r'\(\d{4}\)\s*$')
badchars = re.compile(r'[^a-z0-9 ]', re.I)

def normalize(name):
    """Normalize city name for easy comparison"""
    name = stripHTML(name)
    name = year.sub('', name)
    name = badchars.sub(' ', name)
    name = name.lower()
    name = name.strip()
    name = whitespace.sub(' ', name)
    return name

if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
