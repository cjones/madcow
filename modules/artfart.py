#!/usr/bin/env python

"""Get a random offensive ASCII art"""

from include.utils import Module, stripHTML
from include.useragent import geturl
import re
from urlparse import urljoin
import random
import urllib
import logging as log

class Main(Module):
    pattern = re.compile(r'^\s*artfart(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True
    help = 'artfart - displays some offensive ascii art'
    baseurl = 'http://www.asciiartfarts.com/'
    random_url = urljoin(baseurl, 'random.cgi')
    artfart = re.compile(r'<h1>#<a href="\S+.html">\d+</a>: (.*?)</h1>.*?<pre>(.*?)</pre>', re.DOTALL)

    def response(self, nick, args, kwargs):
        query = args[0]
        if query is None or query == '':
            url = self.random_url
        else:
            query = ' '.join(query.split())
            query = query.replace(' ', '_')
            query = urllib.quote(query) + '.html'
            url = urljoin(self.baseurl, query)
        try:
            doc = geturl(url)
            results = self.artfart.findall(doc)
            result = random.choice(results)
            title, art = result
            art = stripHTML(art)
            return '>>> %s <<<\n%s' % (title, art)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: I had a problem with that, sorry." % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
