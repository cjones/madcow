"""Texts from last night"""

import random
import re
from BeautifulSoup import BeautifulSoup
from madcow.util import strip_html, Module
from madcow.util.text import *
import re

url = 'http://www.textsfromlastnight.com/random/'

class Main(Module):

    pattern = re.compile(r'^\s*(?:txt|texts|tfln)\s*$', re.I)
    help = 'txt - random texts from last night'

    def response(self, nick, args, kwargs):
        kwargs['req'].quoted = True
        soup = self.getsoup(url)
        posts = soup.body('div', 'content')
        contents = []
        for post in posts:
            a = post.find('a', href=re.compile(r'Text-Replies'))
            if a is not None:
                content = u' '.join(strip_html(decode(a.renderContents())).strip().splitlines())
                contents.append(content)
        return random.choice(contents)
