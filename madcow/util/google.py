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

"""Google interface"""

from urlparse import urljoin
import urllib2
import re

from BeautifulSoup import BeautifulSoup
from madcow.util import strip_html, superscript
from madcow.util.http import UserAgent
from madcow.util.textenc import encode, decode

__version__ = '0.3'
__author__ = 'cj_ <cjones@gruntle.org>'

class NonRedirectResponse(Exception):

    """Raised when google doesn't return a redirect"""


class Response(object):

    def __init__(self, data=u''):
        self.data = data

    def read(self, *args, **kwargs):
        return self.data


class NoRedirects(urllib2.HTTPRedirectHandler):

    """Override auto-follow of redirects"""

    def redirect_request(self, *args, **kwargs):
        pass


class NoErrors(urllib2.HTTPDefaultErrorHandler):

    """Don't allow urllib to throw an error on 30x code"""

    def http_error_default(self, req, fp, code, msg, headers):
        return Response(data=dict(headers.items())[u'location'])


class Google(object):

    baseurl = u'http://www.google.com/'
    search = urljoin(baseurl, u'/search')
    luckyopts = {u'hl': u'en', u'btnI': u'I', u'aq': u'f', u'safe': u'off'}
    calcopts = {u'hl': u'en', u'safe': u'off', u'c2coff': 1, u'btnG': u'Search'}
    reConversionDetected = re.compile(u'More about (calculator|currency)')
    reConversionResult = re.compile(u'<h2 class=r.*?>.*?<b>(.*?)<\/b><\/h2>')
    sup_re = re.compile(r'(<sup>.*?</sup>)', re.I | re.DOTALL)
    clock_re = re.compile(r'/images/icons/onebox/clock')
    sun_re = re.compile(r'/images/icons/onebox/weather_sun')
    whitespace_re = re.compile(r'\s{2,}')

    def __init__(self):
        self.ua = UserAgent(handlers=[NoRedirects, NoErrors], agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.215 Safari/535.1")

    def lucky(self, query):
        """Return I'm Feeling Lucky URL for given query"""
        opts = dict(self.luckyopts.items())
        opts[u'q'] = query
        result = self.ua.open(self.search, opts=opts, referer=self.baseurl,
                              size=1024)
        if not result.startswith(u'http'):
            raise NonRedirectResponse
        return result

    calc_re = re.compile(r'calculator')
    white_re = re.compile(r'\s+')

    def calculator(self, query):
        """Try to use google calculator for given query"""
        opts = dict(self.calcopts)
        opts[u'q'] = query
        doc = self.ua.open(self.search, opts=opts)
        soup = BeautifulSoup(doc)
        response = soup.find('img', src=self.calc_re).parent.findNext('h2').renderContents()
        response = ' '.join(response.splitlines())
        response = decode(response, 'utf-8')

        # turn super scripts into utf8
        parts = []
        for part in self.sup_re.split(response):
            if self.sup_re.match(part):
                part = superscript(part)
            parts.append(part)
        response = u''.join(parts)
        response = self.white_re.sub(' ', strip_html(response).strip())
        return response

    def sunrise_sunset(self, query, location):
        """Ask google for the sunrise or sunset from location"""
        soup = BeautifulSoup(self.ua.open(self.search, {'q': '%s in %s' % (query, location)}))
        image = soup.find('img', src=self.sun_re)
        row1 = image.findNext('td')
        row2 = row1.findNext('td')
        result = strip_html(u'%s (%s)' % (self.decode(row1), self.decode(row2)))
        return self.whitespace_re.sub(u' ', result.strip())

    def clock(self, query):
        """Use google to look up time in a given location"""
        try:
            doc = self.ua.open(self.search, {'q': 'time in %s' % query})
            soup = BeautifulSoup(doc)
            table = soup.find('table', 'obcontainer')
            time = table.find('td', style='font-size:medium')
            return strip_html(self.decode(time).strip())
        except:
            raise

    @staticmethod
    def decode(node):
        return decode(node.renderContents())
