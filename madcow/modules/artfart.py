#!/usr/bin/env python

"""Get a random offensive ASCII art"""

from urlparse import urljoin
import re
import random
import urllib
from madcow.util import Module, strip_html
from madcow.util.http import geturl

class Main(Module):

    pattern = re.compile(r'^\s*artfart(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True
    help = u'artfart - displays some offensive ascii art'
    baseurl = u'http://www.asciiartfarts.com/'
    random_url = urljoin(baseurl, u'random.cgi')
    artfart = re.compile(r'<h1>#<a href="\S+.html">\d+</a>: (.*?)</h1>.*?(<pre>.*?</pre>)', re.DOTALL)
    error = u"I had a problem with that, sorry."

    def response(self, nick, args, kwargs):
        query = args[0]
        if query is None or query == u'':
            url = self.random_url
        else:
            query = u' '.join(query.split())
            query = query.replace(u' ', u'_')
            query = urllib.quote(query) + u'.html'
            url = urljoin(self.baseurl, query)
        doc = geturl(url)
        results = self.artfart.findall(doc)
        result = random.choice(results)
        title, art = result
        art = strip_html(art)
        return u'>>> %s <<<\n%s' % (title, art)
