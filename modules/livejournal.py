#!/usr/bin/env python

"""get a random lj"""

import re
from include import rssparser
from include.utils import Module, stripHTML, isUTF8
from include.useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):
    enabled = True
    pattern = re.compile('^\s*(?:livejournal|lj)(?:\s+(\S+))?')
    require_addressing = True
    help = 'lj [user] - get latest entry to an lj, omit user for a random one'
    baseURL = 'http://livejournal.com'
    randomURL = urljoin(baseURL, '/random.bml')
    max = 800

    def response(self, nick, args, kwargs):
        try:
            try:
                user = args[0]
            except:
                user = None

            if user is None or user == '':
                doc = geturl(self.randomURL)
                user = re.search('"currentJournal": "(.*?)"', doc).group(1)

            url = urljoin(self.baseURL, '/users/%s/data/rss' % user)
            feed = rssparser.parse(url)

            # get latest entry and their homepage url
            entry = feed['items'][0]['description']
            page = feed['channel']['link']

            # strip out html
            entry = stripHTML(entry)

            # detect unusual amounts of high ascii, probably russian journal
            if isUTF8(entry):
                return '%s: Russian LJ :(' % nick

            # these can get absurdly long
            entry = entry[:self.max]

            return '%s: [%s] %s' % (nick, page, entry)

        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: Couldn't load the page LJ returned D:" % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
