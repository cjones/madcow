#!/usr/bin/env python

"""Texts from last night"""

import logging as log
import random
import re
from include.BeautifulSoup import BeautifulSoup
from include.useragent import getsoup
from include.utils import stripHTML
from include.utils import Module
import re

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'

url = 'http://www.textsfromlastnight.com/random/'
spam_re = re.compile(r'\s*http://tfl.nu/.*$')

class Main(Module):

    pattern = re.compile(r'^\s*(?:txt|texts|tfln)\s*$', re.I)
    help = 'txt - random texts from last night'

    def response(self, nick, args, kwargs):
        try:
            return u'%s: %s' % (nick, get_text())
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, error)


def get_text():
    text = random.choice(getsoup(url).body.find('ul', id='texts-list')('div', 'text')).textarea
    return spam_re.sub(u'', text.renderContents().decode('utf-8'))


if __name__ == u'__main__':
    from include.utils import test_module
    import sys
    sys.argv.append('txt')
    test_module(Main)
