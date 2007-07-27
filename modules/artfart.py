#!/usr/bin/env python

# Get a random offensive ASCII art

import sys
import re
import urllib
import re
import random
from include import utils

# class for this module
class MatchObject(object):
    def __init__(self, config=None, ns='default', dir=None):
        self.enabled = True                # True/False - enabled?
        self.pattern = re.compile(r'^\s*artfart(?:\s+(.+?))?\s*$', re.I)
        self.requireAddressing = True            # True/False - require addressing?
        self.thread = True                # True/False - should bot spawn thread?
        self.wrap = False                # True/False - wrap output?
        self.help = 'artfart - displays some offensive ascii art'

        self.baseURL = 'http://www.asciiartfarts.com/'
        self.randomURL = self.baseURL + 'random.cgi'
        self.artfart = re.compile(r'<h1>#<a href="\S+.html">\d+</a>: (.*?)</h1>.*?<pre>(.*?)</pre>', re.DOTALL)

    # function to generate a response
    def response(self, *args, **kwargs):
        nick = kwargs['nick']
        query = kwargs['args'][0]
        if query is None or query == '':
            url = self.randomURL
        else:
            query = ' '.join(query.split())
            query = query.replace(' ', '_')
            query = urllib.quote(query) + '.html'
            url = self.baseURL + query

        try:
            doc = urllib.urlopen(url).read()
            results = self.artfart.findall(doc)
            result = random.choice(results)
            title, art = result
            art = utils.stripHTML(art)
            return '>>> %s <<<\n%s' % (title, art)
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: I had a problem with that, sorry." % nick


# this is just here so we can test the module from the commandline
def main(argv = None):
    if argv is None: argv = sys.argv[1:]
    obj = MatchObject()
    print obj.response(nick='testUser', args=argv)

    return 0

if __name__ == '__main__': sys.exit(main())
