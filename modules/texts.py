#!/usr/bin/env python

"""Texts from last night"""

import logging as log
import random
import re
from include.BeautifulSoup import BeautifulSoup
from include.useragent import geturl
from include.utils import stripHTML
from include.utils import Module

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'

url = 'http://www.textsfromlastnight.com/random/'

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
    page = geturl(url)
    soup = BeautifulSoup(page)
    texts = soup.body.findAll('div', 'post_content')
    text = random.choice(texts)
    text = text.renderContents()
    text = stripHTML(text)
    text = text.splitlines()
    text = [line.strip() for line in text]
    text = [line for line in text if line]
    text = u'\n'.join(text)
    return text


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
