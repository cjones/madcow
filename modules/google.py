#!/usr/bin/env python

"""I'm feeling lucky"""

import sys
import urllib
import urllib2
import os
from include.utils import Base
from urlparse import urljoin
import re

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'

class NoRedirects(urllib2.HTTPRedirectHandler):
    """Override auto-follow of redirects"""

    def redirect_request(self, *args, **kwargs):
        pass


class NoErrors(urllib2.HTTPDefaultErrorHandler):    
    """Don't allow urllib to throw an error on 30x code"""

    def http_error_default(self, req, fp, code, msg, headers): 
        return dict(headers.items())['location']


class Google(Base):
    _base_url = 'http://www.google.com/'
    _search_url = urljoin(_base_url, '/search')
    _agent = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
    _lucky_opts = {'hl': 'en', 'btnI': 'I', 'aq': 'f', 'safe': 'off'}

    def __init__(self):
        self.opener = urllib2.build_opener(NoRedirects, NoErrors)

    def lucky(self, query):
        opts = self._lucky_opts
        opts['q'] = query
        url = self._search_url + '?' + urllib.urlencode(opts)
        request = urllib2.Request(url)
        request.add_header('User-Agent', self._agent)
        request.add_header('Referer', self._base_url)
        result = self.opener.open(request)
        if isinstance(result, str):
            return '%s = %s' % (query, result)
        else:
            raise Exception('No matches for ' + query)


class Main(Base):
    enabled = True
    pattern = re.compile('^\s*google\s+(.*?)\s*$')
    require_addressing = True


    help = "google <query> - i'm feeling lucky"

    def __init__(self, *args, **kwargs):
        self.google = Google()

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

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
    sys.exit(main())
