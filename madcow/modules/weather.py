"""Get weather report"""

import re
from madcow.util import strip_html, Module, encoding
from madcow.util.http import geturl
from madcow.util.textenc import *
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup
import feedparser
from learn import Main as Learn
from madcow.util.color import ColorLib

USAGE = u'set location <nick> <location>'

class Weather(object):

    baseurl = u'http://www.wunderground.com/'
    search = urljoin(baseurl, u'/cgi-bin/findweather/getForecast')
    _rss_link = {u'type': u'application/rss+xml'}
    _tempF = re.compile(u'(-?[0-9.]+)\s*\xb0\s*F', re.I)
    _bar = re.compile(r'\s*\|\s*')
    _keyval = re.compile(r'^\s*(.*?)\s*:\s*(.*?)\s*$')

    def __init__(self, colorlib):
        self.colorlib = colorlib

    def forecast(self, location):
        page = geturl(url=self.search, opts={u'query': location},
                      referer=self.baseurl)
        soup = BeautifulSoup(page)

        # disambiguation page
        if u'Search Results' in unicode(soup):
            table = soup.find(u'table', attrs={u'class': u'dataTable'})
            tbody = soup.find(u'tbody')
            results = [row.findAll(u'td')[0].find(u'a')
                       for row in tbody.findAll(u'tr')]
            results = [(normalize(unicode(result.contents[0])),
                        urljoin(Weather.baseurl, unicode(result[u'href'])))
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

        title = soup.find(u'h1').string.strip()
        rss_url = soup.find(u'link', attrs=self._rss_link)[u'href']
        rss = feedparser.parse(rss_url)
        conditions = rss.entries[0].description

        # XXX ok, here's the deal. this page has raw utf-8 bytes encoded
        # as html entities, and in some cases latin1.  this demonstrates a
        # total misunderstanding of how unicode works on the part of the
        # authors, so we need to jump through some hoops to make it work
        conditions = conditions.encode(u'raw-unicode-escape')
        conditions = strip_html(conditions)
        conditions = encoding.convert(conditions)
        fields = self._bar.split(conditions)
        data = {}
        for field in fields:
            try:
                key, val = self._keyval.search(field).groups()
                data[key] = val
            except:
                pass

        try:
            temp = float(self._tempF.search(data[u'Temperature']).group(1))
            blink = False
            if temp < 0:
                color = u'magenta'
            elif temp >=0 and temp < 40:
                color = u'blue'
            elif temp >= 40 and temp < 60:
                color = u'cyan'
            elif temp >= 60 and temp < 80:
                color = u'green'
            elif temp >= 80 and temp < 90:
                color = u'yellow'
            elif temp >= 90 and temp < 100:
                color = u'red'
            elif temp >= 100:
                color = u'red'
                blink = True
            data[u'Temperature'] = self.colorlib.get_color(color,
                    text=data[u'Temperature'])

            # XXX this seems ill-conceived
            if blink:
                data[u'Temperature'] = u'\x1b[5m' + data[u'Temperature'] + \
                        u'\x1b[0m'

        except Exception, error:
            self.log.exception(error)

        output = []
        for key, val in data.items():
            line = u'%s: %s' % (key, val)
            output.append(line)
        output = u' | '.join(output)
        return u'%s: %s' % (title, output)


class Main(Module):

    pattern = re.compile(u'^\s*(?:fc|forecast|weather)(?:\s+(.*)$)?')
    require_addressing = True
    help = u'fc [location] - look up weather forecast'
    error = u"Couldn't find that place, maybe a bomb dropped on it"

    def init(self):
        colorlib = self.madcow.colorlib
        self.weather = Weather(colorlib)
        self.learn = Learn(madcow=self.madcow)

    def response(self, nick, args, kwargs):
        query = args[0]
        if not query:
            location = self.learn.lookup('location', nick)
        elif query.startswith('@'):
            location = self.learn.lookup('location', query[1:])
        else:
            location = query
        if location:
            message = self.weather.forecast(location)
        else:
            message = u"I couldn't look that up"
        return u'%s: %s' % (nick, message)


whitespace = re.compile(r'\s+')
year = re.compile(r'\(\d{4}\)\s*$')
badchars = re.compile(r'[^a-z0-9 ]', re.I)

def normalize(name):
    """Normalize city name for easy comparison"""
    name = strip_html(name)
    name = year.sub(u'', name)
    name = badchars.sub(u' ', name)
    name = name.lower()
    name = name.strip()
    name = whitespace.sub(u' ', name)
    return name
