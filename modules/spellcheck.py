#!/usr/bin/env python

"""Spellcheck using google"""

from include.utils import Module
import logging as log
import re
from include.google import Google

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Christopher Jones'
__all__ = []

class Main(Module):
    pattern = re.compile(r'^\s*spell(?:\s*check)?\s+(\w+)\s*$', re.I)
    help = 'spellcheck <word> - use google to spellcheck'

    def __init__(self, madcow=None):
        self.google = Google()

    def response(self, nick, args, **kwargs):
        try:
            query = args[0]
            corrected = self.google.spellcheck(query)
            if query.lower() == corrected.lower():
                result = 'spelled correctly'
            else:
                result = corrected
            return '%s: %s' % (nick, result)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
