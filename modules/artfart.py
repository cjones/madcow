#!/usr/bin/env python

"""
Get a random offensive ASCII art
"""

import sys
import re
import urllib
import re
import random
from include import utils
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile(r'^\s*artfart(?:\s+(.+?))?\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'artfart - displays some offensive ascii art'

        self.baseURL = 'http://www.asciiartfarts.com/'
        self.randomURL = self.baseURL + 'random.cgi'
        self.artfart = re.compile(r'<h1>#<a href="\S+.html">\d+</a>: (.*?)</h1>.*?<pre>(.*?)</pre>', re.DOTALL)

    def response(self, **kwargs):
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


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
