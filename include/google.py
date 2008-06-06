"""Google interface"""

import urllib2
from utils import Base, Error, stripHTML
from useragent import UserAgent
from urlparse import urljoin
import re

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'

class NonRedirectResponse(Error):
    """Raised when google doesn't return a redirect"""


class Response(Base):

    def __init__(self, data=''):
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
        return Response(data=dict(headers.items())['location'])


class Google(Base):
    baseurl = 'http://www.google.com/'
    search = urljoin(baseurl, '/search')
    luckyopts = {'hl': 'en', 'btnI': 'I', 'aq': 'f', 'safe': 'off'}
    calcopts = {'hl': 'en', 'safe': 'off', 'c2coff': 1, 'btnG': 'Search'}
    spellcheck_opts = {'hl': 'en', 'aq': 'f', 'safe': 'off'}
    correct = re.compile(r'Did you mean.*?:.*?</font>.*?<a.*?>\s*(.*?)\s*</a>',
            re.I + re.DOTALL)
    reConversionDetected = re.compile('More about (calculator|currency)')
    reConversionResult = re.compile('<h2 class=r>.*?<b>(.*?)<\/b><\/h2>')

    def __init__(self):
        self.ua = UserAgent(handlers=[NoRedirects, NoErrors])

    def lucky(self, query):
        opts = dict(self.luckyopts.items())
        opts['q'] = query
        result = self.ua.openurl(self.search, opts=opts, referer=self.baseurl,
                size=1024)
        if not result.startswith('http'):
            raise NonRedirectResponse
        return '%s = %s' % (query, result)

    def spellcheck(self, query):
        opts = dict(self.spellcheck_opts)
        opts['q'] = query
        result = self.ua.openurl(self.search, opts=opts, referer=self.baseurl)
        try:
            result = self.correct.search(result).group(1)
            result = stripHTML(result)
        except:
            result = query
        return result

    def calculator(self, query):
        opts = dict(self.calcopts)
        opts['q'] = query
        doc = self.ua.openurl(self.search, opts=opts)
        if not self.reConversionDetected.search(doc):
            raise Exception, 'no conversion detected'
        response = self.reConversionResult.search(doc).group(1)
        response = stripHTML(response)
        return response

