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
from utils import stripHTML
import useragent
from urlparse import urljoin
import re

__version__ = u'0.1'
__author__ = u'cj_ <cjones@gruntle.org>'

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

    def __init__(self):
        self.ua = useragent.UserAgent(handlers=[NoRedirects, NoErrors])

    def lucky(self, query):
        opts = dict(self.luckyopts.items())
        opts[u'q'] = query
        result = self.ua.open(self.search, opts=opts, referer=self.baseurl,
                              size=1024)
        if not result.startswith(u'http'):
            raise NonRedirectResponse
        return result

    def spellcheck(self, query):
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
        opts = dict(self.calcopts)
        opts[u'q'] = query
        doc = self.ua.open(self.search, opts=opts)
        if not self.reConversionDetected.search(doc):
            raise Exception, u'no conversion detected'
        response = self.reConversionResult.search(doc).group(1)
        response = stripHTML(response)
        return response

