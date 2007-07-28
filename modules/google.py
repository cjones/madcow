#!/usr/bin/env python

"""
I'm feeling lucky
"""

import sys
import re
import urllib
import urllib2
import os


class NoRedirects(urllib2.HTTPRedirectHandler):
    """
    Override auto-follow of redirects
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        pass


class NoErrors(urllib2.HTTPDefaultErrorHandler):    
    """
    Don't allow urllib to throw an error on 30x code
    """

    def http_error_default(self, req, fp, code, msg, headers): 
        return dict(headers.items())['location']


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*google\s+(.+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = "google <query> - i'm feeling lucky"

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            query = args[0]
            url = 'http://www.google.com/search?btnI=I&' + urllib.urlencode({'q' : query})
            request = urllib2.Request(url)
            request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
            result = urllib2.build_opener(NoRedirects, NoErrors).open(request)
            if isinstance(result, str):
                return '%s: %s = %s' % (nick, query, result)
            else:
                raise Exception('No matches for ' + query)
            o
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: Not so lucky today.. %s' % (nick, e)


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
