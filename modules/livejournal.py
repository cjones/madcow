#!/usr/bin/env python

"""
get a random lj
"""

import sys
import re
import urllib
from include import rssparser
from include import utils
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:livejournal|lj)(?:\s+(\S+))?')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'lj [user] - get latest entry to an lj, omit user for a random one'

        self.baseURL = 'http://livejournal.com'
        self.max = 800
    
    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            try: user = args[0]
            except: user = None

            if user is None or user == '':
                # load random page, will redirect
                url = self.baseURL + '/random.bml'
                doc = urllib.urlopen(url).read()

                # find username and load their rss feed with mark pilgrim's rssparser
                user = re.search('"currentJournal": "(.*?)"', doc).group(1)

            url = '%s/users/%s/data/rss' % (self.baseURL, user)
            feed = rssparser.parse(url)

            # get latest entry and their homepage url
            entry = feed['items'][0]['description']
            page = feed['channel']['link']

            # strip out html
            entry = utils.stripHTML(entry)

            # detect unusual amounts of high ascii, probably russian journal
            if utils.isUTF8(entry):
                return '%s: Russian LJ :(' % nick

            # these can get absurdly long
            entry = entry[:self.max]

            return '%s: [%s] %s' % (nick, page, entry)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Couldn't load the page LJ returned D:" % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
