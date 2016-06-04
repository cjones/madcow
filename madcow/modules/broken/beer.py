"""Restaraunt reviews"""

from madcow.util import Module
from urlparse import urljoin
import re

class Main(Module):

    pattern = re.compile(r'^\s*beer\s+(.+?)\s*$', re.I)
    help = 'beer <query> - BEER'

    def response(self, nick, args, kwargs):
        page = self.getsoup('http://beeradvocate.com/search', {'q': args[0], 'qt': 'beer', 'ls': 'Y', 'retired': 'N'})
        page = page.find('div', id='baContent')
        page = self.getsoup(urljoin('http://beeradvocate.com/', page.ul.findAll('li')[0].a['href']))
        return page.find('meta', property='og:description')['content']
