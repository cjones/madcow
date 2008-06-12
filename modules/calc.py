#!/usr/bin/env python

"""Use Google as a calculator"""

import re
from include.utils import Module
from include.google import Google
import logging as log

class Main(Module):
    pattern = re.compile('^\s*calc\s+(.+)', re.I)
    require_addressing = True
    help = 'calc <expression> - pass expression to google calculator'

    def __init__(self, madcow=None):
        self.google = Google()

    def response(self, nick, args, kwargs):
        try:
            query = args[0]
            response = self.google.calculator(query)
            return '%s: %s' % (nick, response)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: No results (bad syntax?)' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
