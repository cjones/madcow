"""RSS generation"""

import datetime

from django.conf import settings
from django.core.urlresolvers import reverse

from gruntle.memebot.rss.generator import RSSItem, RSS2, Image
from gruntle.memebot.models import SerializedData, Link
from gruntle.memebot.decorators import logged, locked
from gruntle.memebot.utils import first, local_to_gmt

class LinkItem(RSSItem):

    """A single Link feed item"""

    def __init__(self, link):
        # TODO i think description should get set to the rendered page? somehow..
        super(LinkItem, self).__init__(
                title=first(link.title, link.resolved_url, link.url, 'n/a'),
                link=first(link.resolved_url, link.url),
                guid=link.guid,
                pubDate=local_to_gmt(link.created))


class LinkFeed(RSS2):

    """A feed generator for Link objects"""

    def __init__(self, links):
        now = local_to_gmt(datetime.datetime.now())

        if settings.RSS_IMAGE is None:
            image = None
        else:
            image_url, image_title, image_link = settings.RSS_IMAGE
            image = Image(url=image_url, title=image_title, link=image_link)

        super(LinkFeed, self).__init__(
                title=settings.RSS_TITLE,
                link=reverse('index'),
                description=settings.RSS_DESCRIPTION,
                language=settings.LANGUAGE_CODE,
                copyright=settings.RSS_COPYRIGHT,
                pubDate=now,
                lastBuildDate=now,
                image=image,
                items=[LinkItem(link) for link in links])


class Feed(object):

    """Base Feed class"""


def get_feeds(names):
    """Import configured feeds"""
    func_name = 'feed'
    global_context = globals()
    local_context = locals()
    feeds = []
    for name in names:
        mod = __import__(name, global_context, local_context, [func_name])
        feed = getattr(mod, func_name, None)
        if feed is not None:
            feeds.append((name, feed))
    return feeds


@logged('build-rss', append=True)
@locked('build-rss', 0)
def rebuild_rss(
        log,
        max_links=None,
        num_links=None,
        ):

    """Rebuild all RSS feeds"""

    feeds = get_feeds(settings.FEEDS)
