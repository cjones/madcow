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

import urllib2
from utils import stripHTML, superscript
import useragent
from urlparse import urljoin
import re

__version__ = '0.2'
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
    spellcheck_opts = {u'hl': u'en', u'aq': u'f', u'safe': u'off'}
    correct = re.compile(r'Did you mean.*?:.*?</font>.*?<a.*?>\s*(.*?)\s*</a>',
                         re.I | re.DOTALL)
    reConversionDetected = re.compile(u'More about (calculator|currency)')
    reConversionResult = re.compile(u'<h2 class=r>.*?<b>(.*?)<\/b><\/h2>')
    extra_re = re.compile(r'<div id=res class=med>(.*?)</div>', re.DOTALL)
    table_re = re.compile(r'<table.*?>(.*?)</table>', re.DOTALL | re.I)
    rows_re = re.compile(r'<tr.*?>(.*?)</tr>', re.DOTALL | re.I)
    cells_re = re.compile(r'<td.*?>(.*?)</td>', re.DOTALL | re.I)
    br_re = re.compile(r'<br.*?>', re.DOTALL | re.I)
    sup_re = re.compile(r'(<sup>.*?</sup>)', re.I | re.DOTALL)

    def __init__(self):
        self.ua = useragent.UserAgent(handlers=[NoRedirects, NoErrors])

    def lucky(self, query):
        """Return I'm Feeling Lucky URL for given query"""
        opts = dict(self.luckyopts.items())
        opts[u'q'] = query
        result = self.ua.open(self.search, opts=opts, referer=self.baseurl,
                              size=1024)
        if not result.startswith(u'http'):
            raise NonRedirectResponse
        return result

    def spellcheck(self, query):
        """Look for "did you mean?" response for given query"""
        opts = dict(self.spellcheck_opts)
        opts[u'q'] = query
        result = self.ua.open(self.search, opts=opts, referer=self.baseurl)
        try:
            result = self.correct.search(result).group(1)
            result = stripHTML(result)
        except AttributeError:
            result = query
        return result

    def calculator(self, query):
        """Try to use google calculator for given query"""
        opts = dict(self.calcopts)
        opts[u'q'] = query
        doc = self.ua.open(self.search, opts=opts)
        if not self.reConversionDetected.search(doc):
            raise Exception, u'no conversion detected'
        response = self.reConversionResult.search(doc).group(1)

        # turn super scripts into utf8
        parts = []
        for part in self.sup_re.split(response):
            if self.sup_re.match(part):
                part = superscript(part)
            parts.append(part)
        response = u''.join(parts)

        return stripHTML(response)

    def clock(self, query):
        """Use google to look up time in a given location"""
        try:
            doc = self.ua.open(self.search, {'q': 'time in %s' % query})
            extra = self.extra_re.search(doc).group(1)
            table = self.table_re.search(extra).group(1)
            row = self.rows_re.findall(table)[0]
            cells = self.cells_re.findall(row)
            if 'alt="Clock"' not in cells[0]:
                raise Exception
            line = self.br_re.split(cells[1])[0]
            return stripHTML(line)
        except:
            pass

