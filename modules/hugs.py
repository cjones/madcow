#!/usr/bin/env python

"""
Get a random confession from grouphug.us
"""

import sys
import re
import urllib, urllib2, cookielib
from include import utils
import os
from include.BeautifulSoup import BeautifulSoup
import random

AGENT = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'

class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*hugs(?:\s+(\d+))?')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'hugs - random confession'

        # build opener to mimic browser
        cj = cookielib.CookieJar()
        ch = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(ch)
        opener.addheaders = [('User-Agent', AGENT)]
        self.opener = opener

    def response(self, **kwargs):
        try:
            nick = kwargs['nick']
            args = kwargs['args']

            if args[0] is not None:
                url = 'http://beta.grouphug.us/confessions/' + args[0]
            else:
                url = 'http://beta.grouphug.us/random'

            url = 'http://beta.grouphug.us/random'

            # load page
            req = urllib2.Request(url)
            res = self.opener.open(req)
            doc = res.read()

            soup = BeautifulSoup(doc)
            confs = soup.findAll('div', attrs={'class': 'content'})[3:]
            conf = random.choice(confs)
            content = []
            for p in conf.findAll('p'):
                content.append(str(p))
            conf = ' '.join(content)

            conf = utils.stripHTML(conf)
            conf = conf.strip()

            return conf

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: I had some issues with that..' % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
