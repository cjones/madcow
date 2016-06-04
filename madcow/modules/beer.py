"""Restaraunt reviews"""

from madcow.util import Module
from urlparse import urljoin
import re

class Main(Module):

    baseurl = 'http://beeradvocate.com/'
    searchurl = baseurl + 'search'
    pattern = re.compile(r'^\s*beer\s+(.+?)\s*$', re.I)
    help = 'beer <query> - BEER'

    def response(self, nick, args, kwargs):
        page = self.getsoup(self.searchurl, q=args[0], qt='beer', retired='N')
        content = page.find('div', id='ba-content')
        url = urljoin(self.baseurl, content.ul.li.a['href'])
        page = self.getsoup(url)
        return page.find('meta', property='og:description')['content']
