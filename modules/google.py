#!/usr/bin/env python

"""I'm feeling lucky"""

import sys
import urllib
import urllib2
from include.utils import Base, Module
from include.useragent import UserAgent
from urlparse import urljoin
import re

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'

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

    def __init__(self):
        self.ua = UserAgent(handlers=[NoRedirects, NoErrors])

    def lucky(self, query):
        opts = dict(self.luckyopts.items())
        opts['q'] = query
        try:
            result = self.ua.openurl(self.search, opts=opts,
                    referer=self.baseurl, size=1024)
            if not result.startswith('http'):
                raise Exception, 'non-redirect response'
            return '%s = %s' % (query, result)

        except Exception, e:
            print >> sys.stderr, e
            return 'No matches'


class Main(Module):
    pattern = re.compile('^\s*google\s+(.*?)\s*$')
    require_addressing = True
    help = "google <query> - i'm feeling lucky"

    def __init__(self, *args, **kwargs):
        self.google = Google()

    def response(self, nick, args, **kwargs):
        try:
            query = args[0]
            return '%s: %s' % (nick, self.google.lucky(query))
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: Not so lucky today.. %s' % (nick, e)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    import os
    sys.exit(main())
