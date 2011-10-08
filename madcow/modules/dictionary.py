#!/usr/bin/env python

"""Look up word definitions"""

from urlparse import urljoin
from urllib import quote
import re
from madcow.util.http import getsoup
from madcow.util import strip_html, Module
from madcow.util.text import *

class Main(Module):

    pattern = re.compile(r'^\s*def(?:ine)?\s+(.+?)\s*$', re.I)
    help = 'define <term> - get a definition'
    base_url = 'http://definr.com/'
    define_url = urljoin(base_url, '/definr/show/toe')
    whitespace_re = re.compile(r'\s{2,}')
    error = u'Stop making words up'

    def response(self, nick, args, kwargs):
        return u'%s: %s' % (nick, self.lookup(args[0]))

    def lookup(self, term, idx=1):
        """Lookup term in dictionary"""
        url = urljoin(self.define_url, quote(term.lower()))
        soup = getsoup(url, referer=self.base_url)
        for br in soup('br'):
            br.extract()
        val = strip_html(decode(soup.renderContents(), 'utf-8'))
        val = val.replace(u'\xa0', ' ').replace('\n', ' ')
        return self.whitespace_re.sub(' ', val).strip()
