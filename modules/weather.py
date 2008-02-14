#!/usr/bin/env python

"""Get weather report"""

import sys
import re
import os
from include.utils import UserAgent
from include.utils import stripHTML
from urlparse import urljoin
from include.BeautifulSoup import BeautifulSoup
from include import rssparser
from learn import MatchObject as Learn

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['Weather', 'MatchObject']
__usage__ = 'set location <nick> <location>'

class Weather(object):
    _base_url = 'http://www.wunderground.com/'
    _search_url = urljoin(_base_url, '/cgi-bin/findweather/getForecast')
    _rss_link = {'type': 'application/rss+xml'}
    _advert = 'Weather Underground RSS Feed for '

    def __init__(self):
        self.ua = UserAgent()

    def forecast(self, location):
        page = self.ua.fetch(url=Weather._search_url, opts={'query': location},
                referer=Weather._base_url, method='GET')
        soup = BeautifulSoup(page)
        rss_url = soup.find('link', attrs=Weather._rss_link)['href']
        rss = rssparser.parse(rss_url)
        title = rss['channel']['description']
        title = title.replace(Weather._advert, '')
        conditions = stripHTML(rss['items'][0]['description'])
        return '%s: %s' % (title, conditions)


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir='..'):
        self.config = config
        self.ns = ns
        self.dir = dir
        self.enabled = True
        self.pattern = re.compile('^\s*(?:fc|forecast|weather)(?:\s+(.*)$)?')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = None
        self.weather = Weather()
        self.learn = Learn(ns=self.ns, dir=self.dir)

    def response(self, **kwargs):
        nick = kwargs['nick']

        try:
            args = kwargs['args'][0]
        except:
            args = None

        if args is None or args == '':
            query = self.learn.lookup('location', nick)
        elif args.startswith('@'):
            query = self.learn.lookup('location', args[1:])
        else:
            query = args

        if query is None or query == '':
            return '%s: unknown nick. %s' % (nick, __usage__)

        try:
            return '%s: %s' % (nick, self.weather.forecast(query))
        except Exception, e:
            return '%s: problem with query: %s' % (nick, e)


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'],
            args=[' '.join(sys.argv[1:])])
    sys.exit(0)
