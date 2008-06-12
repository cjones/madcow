#!/usr/bin/env python

"""Get a random confession from grouphug.us"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
from include.BeautifulSoup import BeautifulSoup
from urlparse import urljoin
import random
import logging as log

class Main(Module):
    pattern = re.compile('^\s*hugs\s*$', re.I)
    require_addressing = True
    help = 'hugs - random confession'
    baseurl = 'http://beta.grouphug.us/'
    random = urljoin(baseurl, '/random')

    def response(self, nick, args, kwargs):
        try:
            doc = geturl(self.random)
            soup = BeautifulSoup(doc)
            confs = soup.findAll('div', attrs={'class': 'content'})[3:]
            conf = random.choice(confs)
            conf = [str(p) for p in conf.findAll('p')]
            conf = ' '.join(conf)
            conf = stripHTML(conf)
            conf = conf.strip()
            return conf
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: I had some issues with that..' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
