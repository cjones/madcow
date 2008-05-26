#!/usr/bin/env python

"""get the current woot - author: Twid"""

from urlparse import urljoin
import re
from include import rssparser
from include.utils import Module, stripHTML
import logging as log

class Main(Module):
    pattern = re.compile('^\s*woot(?:\s+(\S+))?')
    require_addressing = True
    help = 'woot - get latest offer from woot.com'
    baseurl = 'http://woot.com'
    rssurl = urljoin(baseurl, '/Blog/Rss.aspx')
    max = 200

    def response(self, nick, args, **kwargs):
        try:
            feed = rssparser.parse(self.rssurl)

            # get latest entry and their homepage url
            title = feed['items'][0]['title'].split()
            offer = ' '.join(title[:-2])
            
            try:
                price = "$%.2f" % title[-1]
            except:
                price = ''

            longdescription = feed['items'][0]['description']
            page = feed['items'][0]['link']

            # strip out html
            longdescription = stripHTML(longdescription).strip()

            # these can get absurdly long
            if longdescription > self.max:
                longdescription = longdescription[:self.max-4] + ' ...'

            return '%s: %s\n[%s]\n%s' % (offer, price, page, longdescription)

        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: Couldn't load the page woot returned D:" % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
