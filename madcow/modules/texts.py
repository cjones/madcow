"""Texts from last night"""

import random
import re
from BeautifulSoup import BeautifulSoup
from madcow.util.http import getsoup
from madcow.util import strip_html, Module
from madcow.util.textenc import *
import re

url = 'http://www.textsfromlastnight.com/random/'
spam_re = re.compile(r'\s*http://tfl.nu/.*$')

class Main(Module):

    pattern = re.compile(r'^\s*(?:txt|texts|tfln)\s*$', re.I)
    help = 'txt - random texts from last night'

    def response(self, nick, args, kwargs):
        return u'%s: %s' % (nick, get_text())


def get_text():
    text = random.choice(getsoup(url).body.find('ul', id='texts-list')('div', 'text')).textarea
    return spam_re.sub(u'', decode(text.renderContents(), 'utf-8'))
