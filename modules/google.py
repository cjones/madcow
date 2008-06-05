#!/usr/bin/env python

"""I'm feeling lucky"""

from include.google import Google
from include.utils import Module
import re
import logging as log

__version__ = '0.3'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'

class Main(Module):
    pattern = re.compile('^\s*google\s+(.*?)\s*$')
    require_addressing = True
    help = "google <query> - i'm feeling lucky"

    def __init__(self, *args, **kwargs):
        self.google = Google()

    def response(self, nick, args, **kwargs):
        try:
            query = args[0]
            return '%s: %s' % (nick, self.google.lucky(query))
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: Not so lucky today..' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
