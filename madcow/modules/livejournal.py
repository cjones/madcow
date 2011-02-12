"""Read from LiveJournal"""

import re
import feedparser
from madcow.util import Module, strip_html
from madcow.util.http import geturl
from urlparse import urljoin

class Main(Module):

    enabled = True
    pattern = re.compile(u'^\s*(?:livejournal|lj)(?:\s+(\S+))?')
    require_addressing = True
    help = u'lj [user] - get latest entry to an lj, omit user for a random one'
    baseURL = u'http://livejournal.com'
    randomURL = urljoin(baseURL, u'/random.bml')
    max = 800
    error = u"Couldn't load the page LJ returned D:"

    def response(self, nick, args, kwargs):
        try:
            user = args[0]
        except:
            user = None
        if user is None or user == u'':
            doc = geturl(self.randomURL)
            user = re.search(u'"currentJournal":\s*"(.*?)"', doc).group(1)
        url = urljoin(self.baseURL, u'/users/%s/data/rss' % user)
        rss = feedparser.parse(url)
        entry = strip_html(rss.entries[0].description)[:self.max]
        page = strip_html(rss.channel.link)
        return u'%s: [%s] %s' % (nick, page, entry)
