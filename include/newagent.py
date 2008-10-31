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
import re
from utils import stripHTML
import codecs
import chardet
import logging as log

AGENT = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)'
VERSION = sys.version_info[0] * 10 + sys.version_info[1]
UA = None

class UserAgent(object):

    """Closely mimic a browser"""

    meta_re = re.compile(r'<meta\s+(.*?)\s*>', re.I | re.DOTALL)
    attr_re = re.compile(r'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*(\'[^\']*\'|'
                         r'"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~@]*))?')

    def __init__(self, handlers=None, cookies=True, agent=AGENT, timeout=None):
        self.timeout = timeout
        if handlers is None:
            handlers = []
        if cookies:
            handlers.append(urllib2.HTTPCookieProcessor)
        self.opener = urllib2.build_opener(*handlers)
        if agent:
            self.opener.addheaders = [('User-Agent', agent)]

    def open(self, url, opts=None, data=None, referer=None, size=-1,
             timeout=-1):
        """Open URL and return unicode content"""
        url = list(urlparse.urlparse(url))
        if opts:
            query = [urllib.urlencode(opts)]
            if url[4]:
                query.append(url[4])
            url[4] = '&'.join(query)
        request = urllib2.Request(urlparse.urlunparse(url), data)
        if referer:
            request.add_header('Referer', referer)
        if timeout == -1:
            timeout = self.timeout
        args = [request]
        if VERSION < 26:
            self.settimeout(timeout)
        else:
            args.append(timeout)
        response = self.opener.open(*args)
        data = response.read(size)

        # XXX this crap should go in its own library

        # try to figure out the encoding first from meta tags
        charset = self.metacharset(data)
        if charset:
            log.debug('using http meta header encoding: %s' % charset)
            return data.decode(charset, 'replace')

        # if that doesn't work, see if there's a real http header
        if response.headers.plist:
            charset = response.headers.plist[0]
            attrs = self.parseattrs(charset)
            if 'charset' in attrs:
                charset = self.lookup(attrs['charset'])
            if charset:
                log.debug('using http header encoding: %s' % charset)
                return data.decode(charset, 'replace')

        # that didn't work, try chardet library
        charset = self.lookup(chardet.detect(data)['encoding'])
        if charset:
            log.debug('detected encoding: %s' % repr(charset))
            return data.decode(charset, 'replace')

        # if that managed to fail, just use ascii
        log.warn("couldn't detect encoding, using ascii")
        return data.decode('ascii', 'replace')

    @staticmethod
    def lookup(charset):
        """Lookup codec"""
        try:
            return codecs.lookup(charset).name
        except LookupError:
            pass

    @classmethod
    def metacharset(cls, data):
        """Parse data for HTML meta character encoding"""
        for meta in cls.meta_re.findall(data):
            attrs = cls.parseattrs(meta)
            if ('http-equiv' in attrs and
                attrs['http-equiv'].lower() == 'content-type' and
                'content' in attrs):
                content = attrs['content']
                content = cls.parseattrs(content)
                if 'charset' in content:
                    return cls.lookup(content['charset'])

    @classmethod
    def parseattrs(cls, data):
        """Parse key=val attributes"""
        attrs = {}
        for key, rest, val in cls.attr_re.findall(data):
            if not rest:
                val = None
            elif val[:1] == '\'' == val[-1:] or val[:1] == '"' == val[-1:]:
                val = val[1:-1]
                val = stripHTML(val)
            attrs[key.lower()] = val
        return attrs

    @staticmethod
    def settimeout(timeout):
        """Monkey-patch socket timeout if older urllib2"""

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

        import httplib
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
    UA = UserAgent(handlers, cookies, agent, timeout)


def geturl(url, opts=None, data=None, referer=None, size=-1, timeout=-1):
    return getua().open(url, opts, data, referer, size, timeout)

geturl.__doc__ = UserAgent.open.__doc__

