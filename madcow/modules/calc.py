#!/usr/bin/env python

"""Use Google as a calculator"""

import re
from madcow.util import Module
from google import Google

class Main(Module):

    pattern = re.compile(u'^\s*calc\s+(.+)', re.I)
    require_addressing = True
    help = u'calc <expression> - pass expression to google calculator'
    error = 'No results (bad syntax?)'

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        return u'%s: %s' % (nick, self.google.calculator(args[0]))
