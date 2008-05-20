#!/usr/bin/env python

"""Get a random confession from grouphug.us"""

import sys
import re
from include.utils import Module, stripHTML
from include.useragent import geturl
from include.BeautifulSoup import BeautifulSoup
from urlparse import urljoin
import random

class Main(Module):
    pattern = re.compile('^\s*hugs\s*$', re.I)
    require_addressing = True
    help = 'hugs - random confession'
    baseurl = 'http://beta.grouphug.us/'
    random = urljoin(baseurl, '/random')

    def response(self, nick, args, **kwargs):
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
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: I had some issues with that..' % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    import os
    sys.exit(main())
