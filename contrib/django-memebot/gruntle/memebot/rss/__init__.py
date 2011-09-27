"""RSS generation"""

import datetime

from django.conf import settings

from gruntle.memebot.rss.PyRSS2Gen import RSSItem, RSS2, Image
from gruntle.memebot.utils import first, local_to_gmt

class LinkItem(RSSItem):

    """A single Link item represented in RSS"""

    def __init__(self, link):
        # TODO i think description should get set to the rendered page? somehow..
        super(LinkItem, self).__init__(
                title=first(link.title, link.resolved_url, link.url, 'n/a'),
                link=first(link.resolved_url, link.url),
                guid=link.guid,
                pubDate=local_to_gmt(link.created))


class LinkFeed(RSS2):

    """A feed of Links"""

    def __init__(self, links):
        now = local_to_gmt(datetime.datetime.now())

        if settings.RSS_IMAGE is None:
            image = None
        else:
            image_url, image_title, image_link = settings.RSS_IMAGE
            image = Image(url=image_url, title=image_title, link=image_link)

        super(LinkFeed, self).__init__(
                title=settings.RSS_TITLE,
                link='http://grunte.org/TBD/',  # from django.core.urlresolvers import reverse
                description=settings.RSS_DESCRIPTION,
                language=settings.LANGUAGE_CODE,
                copyright=settings.RSS_COPYRIGHT,
                pubDate=now,
                lastBuildDate=now,
                image=image,
                items=[LinkItem(link) for link in links])
