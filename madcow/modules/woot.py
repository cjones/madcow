"""get the current woot - author: Twid"""

import re
import feedparser
from madcow.util import Module, strip_html

class Main(Module):

    pattern = re.compile(u'^\s*woot\s*$', re.I)
    require_addressing = True
    help = u'woot - get latest offer from woot.com'
    url = u'http://woot.com/Blog/Rss.aspx'
    max = 200
    break_re = re.compile(r'\s*[\r\n]+\s*')

    def response(self, nick, args, kwargs):
        rss = feedparser.parse(self.url)
        entry = rss.entries[0]
        title, summary, link = map(
                strip_html, [entry.title, entry.summary, entry.link])
        summary = self.break_re.sub(u' ', summary)
        if len(summary) > self.max:
            summary = summary[:self.max - 4] + u' ...'
        return u'%s [%s] %s' % (title, link, summary)
