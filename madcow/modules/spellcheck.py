"""Spellcheck using google"""

from urlparse import urljoin
import re
from madcow.util import Module, strip_html
from madcow.util.text import *

class Main(Module):

    pattern = re.compile(r'^\s*spell(?:\s*check)?\s+(.+?)\s*$', re.I)
    help = u'spellcheck <word> - use google to spellcheck'
    google_url = 'http://www.google.com/'
    google_search = urljoin(google_url, '/search')
    error = 'I had trouble with that'

    def response(self, nick, args, kwargs):
        opts = {'hl': 'en', 'safe': 'off', 'q': args[0]}
        soup = self.getsoup(self.google_search, opts, referer=self.google_url)
        correct = soup.body.find('a', href=re.compile(r'^/search.*spell=1'))
        if correct:
            res = strip_html(decode(correct.renderContents(), 'utf-8'))
        else:
            res = u'spelled correctly. probably.'
        return u'%s: %s' % (nick, res)
