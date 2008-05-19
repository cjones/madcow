#!/usr/bin/env python

"""Get a random offensive ASCII art"""

from include.utils import Base, UserAgent, stripHTML
import re
from urlparse import urljoin
import sys
import os
import random
import urllib

class Main(Base):
    enabled = True
    pattern = re.compile(r'^\s*artfart(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True


    help = 'artfart - displays some offensive ascii art'

    base_url = 'http://www.asciiartfarts.com/'
    random_url = urljoin(base_url, 'random.cgi')
    artfart = re.compile(r'<h1>#<a href="\S+.html">\d+</a>: (.*?)</h1>.*?<pre>(.*?)</pre>', re.DOTALL)

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.ua = UserAgent()

    def response(self, nick, args, **kwargs):
        query = args[0]
        if query is None or query == '':
            url = self.random_url
        else:
            query = ' '.join(query.split())
            query = query.replace(' ', '_')
            query = urllib.quote(query) + '.html'
            url = urljoin(self.base_url, query)

        try:
            doc = self.ua.fetch(url)
            results = self.artfart.findall(doc)
            result = random.choice(results)
            title, art = result
            art = stripHTML(art)
            return '>>> %s <<<\n%s' % (title, art)
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: I had a problem with that, sorry." % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
