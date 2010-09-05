#!/usr/bin/env python
#
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

"""Closely mimic a browser"""

import sys
import urllib2
import urlparse
import urllib
import logging as log
import encoding
from gzip import GzipFile
import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from BeautifulSoup import BeautifulSoup

AGENT = u'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)'
VERSION = sys.version_info[0] * 10 + sys.version_info[1]
UA = None

class UserAgent(object):

    """Closely mimic a browser"""

    def __init__(self, handlers=None, cookies=True, agent=AGENT):
        if handlers is None:
            handlers = []
        if cookies:
            handlers.append(urllib2.HTTPCookieProcessor)
        self.opener = urllib2.build_opener(*handlers)
        if agent:
            self.opener.addheaders = [(u'User-Agent', agent)]

    def open(self, url, opts=None, data=None, referer=None, size=-1,
             add_headers=None):
        """Open URL and return unicode content"""
        log.debug(u'fetching url: %s' % url)
        url = list(urlparse.urlparse(url))
        if opts:
            for key in opts:
                val = opts[key]
                if isinstance(val, unicode):
                    opts[key] = val.encode('utf-8', 'replace')
            query = [urllib.urlencode(opts)]
            if url[4]:
                query.append(url[4])
            url[4] = u'&'.join(query)
        realurl = urlparse.urlunparse(url)
        #print 'url = %r' % realurl
        request = urllib2.Request(realurl, data)
        if referer:
            request.add_header(u'Referer', referer)
        if add_headers:
            for item in add_headers.items():
                request.add_header(*item)
        response = self.opener.open(request)
        data = response.read(size)

        import google
        if isinstance(response, google.Response):
            headers = None
        else:
            headers = response.headers

        if headers and headers.get('content-encoding') == 'gzip':
            data = GzipFile(fileobj=StringIO(data)).read()

        return encoding.convert(data, headers)

    @staticmethod
    def settimeout(timeout):
        """Monkey-patch socket timeout if older urllib2"""

        import httplib, socket

        def connect(self):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(timeout)
                self.sock.connect((self.host, self.port))
            except socket.error, error:
                if self.sock:
                    self.sock.close()
                self.sock = None
                raise error

        httplib.HTTPConnection.connect = connect


def getua():
    """Returns global user agent instance"""
    global UA
    if UA is None:
        UA = UserAgent()
    return UA


def setup(handlers=None, cookies=True, agent=AGENT, timeout=None):
    """Create global user agent instance"""
    global UA
    UserAgent.settimeout(timeout)
    UA = UserAgent(handlers, cookies, agent)


def geturl(url, opts=None, data=None, referer=None, size=-1, add_headers=None):
    return getua().open(url, opts, data, referer, size, add_headers)


script_re = re.compile(r'<script.*?>.*?</script>', re.I | re.DOTALL)

def getsoup(*args, **kwargs):
    """geturl wrapper to return soup minus scripts/styles"""
    #page = script_re.sub('', page)  # XXX hack for newer version of BS
    #for style in soup('style'): style.extract()
    return BeautifulSoup(geturl(*args, **kwargs))

geturl.__doc__ = UserAgent.open.__doc__
