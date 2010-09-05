"""Get a random confession from grouphug.us"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import geturl
from BeautifulSoup import BeautifulSoup
from urlparse import urljoin
import random

class Main(Module):

    pattern = re.compile(u'^\s*hugs\s*$', re.I)
    require_addressing = True
    help = u'hugs - random confession'
    baseurl = u'http://grouphug.us/'
    random = urljoin(baseurl, u'/random')
    last = re.compile(r'<a href="/frontpage\?page=(\d+)" class="pager-last active"')
    error = u'I had some issues with that..'

    def response(self, nick, args, kwargs):
        doc = geturl(self.random, add_headers={'Accept': '*/*'})
        soup = BeautifulSoup(doc)
        main = soup.find(u'div', attrs={u'id': u'main'})
        confs = main.findAll(u'div', attrs={u'class': u'content'})
        conf = random.choice(confs)
        conf = [unicode(p) for p in conf.findAll(u'p')]
        conf = u' '.join(conf)
        conf = strip_html(conf)
        conf = conf.strip()
        return conf
