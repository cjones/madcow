#!/usr/bin/env python

"""Plugin to return summary from WikiPedia"""

from include.utils import Module
from include.wiki import Wiki
import re
import logging as log

class Main(Module):
    pattern = re.compile('^\s*(?:wp|wiki|wikipedia)\s+(.*?)\s*$', re.I)
    require_addressing = True
    help = 'wiki <term> - look up summary of term on wikipedia'

    def __init__(self, *args, **kwargs):
        self.wiki = Wiki()

    def response(self, nick, args, **kwargs):
        try:
            return self.wiki.get_summary(args)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: problem with query: %s' % (nick, e)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
