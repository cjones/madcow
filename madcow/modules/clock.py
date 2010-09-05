#!/usr/bin/env python

"""Use Google to get time's in various places"""

from madcow.util import Module
from google import Google
import re

class Main(Module):

    pattern = re.compile(r'^\s*(?:clock|time)(?:\s*[:-]\s*|\s+)(.+?)\s*$', re.I)
    help = u'time <location> - ask google what time it is somewhere'
    in_re = re.compile(r'^\s*in\s+', re.I)

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        query = args[0]
        query = self.in_re.sub('', query)
        result = self.google.clock(query)
        if result:
            return u'%s: %s' % (nick, result)
        else:
            return u"%s: They don't do the whole time thing in \"%s\"" % (nick, query)
