#!/usr/bin/env python

# I'm feeling lucky

import sys
import re
import urllib
import urllib2

# need to override some behavior in urllib2, no way to turn off redirects easily
class NoRedirects(urllib2.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        pass

# with redirects off, urllib wants to throw an error for 30x, just return the url
class NoErrors(urllib2.HTTPDefaultErrorHandler):    
    def http_error_default(self, req, fp, code, msg, headers): 
        return dict(headers.items())['location']

# class for this module
class MatchObject(object):
    def __init__(self, config=None, ns='default', dir=None):
        self.enabled = True                # True/False - enabled?
        self.pattern = re.compile('^\s*google\s+(.+)')    # regular expression that needs to be matched
        self.requireAddressing = True            # True/False - require addressing?
        self.thread = True                # True/False - should bot spawn thread?
        self.wrap = False                # True/False - wrap output?
        self.help = "google <query> - i'm feeling lucky"

    # function to generate a response
    def response(self, *args, **kwargs):
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
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: Not so lucky today.. %s' % (nick, e)


# this is just here so we can test the module from the commandline
def main(argv = None):
    if argv is None: argv = sys.argv[1:]
    obj = MatchObject()
    print obj.response(nick='testUser', args=argv)

    return 0

if __name__ == '__main__': sys.exit(main())
