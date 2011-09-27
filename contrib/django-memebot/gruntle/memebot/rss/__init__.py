"""RSS generation"""

import datetime
from django.conf import settings
from gruntle.memebot.rss.PyRSS2Gen import RSSItem, RSS2
from gruntle.memebot.utils import first

class LinkItem(RSSItem):

    """A single Link item represented in RSS"""

    def __init__(self, link):
        super(LinkItem, self).__init__(
                title=first(link.title, link.resolved_url, link.url, 'n/a'),
                link=first(link.resolved_url, link.url),
                guid=link.guid,
                pubDate=link.created)


class LinkFeed(RSS2):

    """A feed of Links"""

    def __init__(self, links):
        super(LinkFeed, self).__init__(
                title=settings.RSS_TITLE,
                description=settings.RSS_DESCRIPTION,
                link='http://grunte.org/TBD/',  # from django.core.urlresolvers import reverse
                lastBuildDate=datetime.datetime.now(),  # XXX probably don't do this.
                items=[LinkItem(link) for link in links])
