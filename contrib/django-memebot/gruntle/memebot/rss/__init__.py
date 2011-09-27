"""RSS generation"""

import datetime

from django.conf import settings

from gruntle.memebot.rss.PyRSS2Gen import RSSItem, RSS2, Image
from gruntle.memebot.models import SerializedData, Link
from gruntle.memebot.decorators import logged, locked
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


@logged('build-rss', append=True)
@locked('build-rss', 0)
def rebuild_rss(
        log,
        max_links=None,
        num_links=None,
        ):

    """Rebuild cached RSS file"""

    if max_links is None:
        max_links = settings.RSS_MAX_LINKS
    if num_links is None:
        num_links = settings.RSS_NUM_LINKS

    log.info('Rebuilding RSS feed ...')

    rss_last_publish_id = SerializedData.data.rss_last_publish_id
    if rss_last_publish_id is None:
        rss_last_publish_id = SerializedData.data.rss_last_publish_id = 0

    # XXX need to rethink this just a bit more.. other ideas:
    #
    # - generic configurable rss feeds with different filters.. sfw, nsfw, images only, no youtube, diff chans etc
    #
    # new_links = Link.objects.filter(state='published', publish_id__gt=rss_last_publish_id).order_by('published')
    # if max_links:
    #     new_links = new_links[:max_links]

    # num_new_links = new_links.count()
    # if not num_new_links:
    #     log.info('No new links to publish, bailing')
    #     return

    # need_links = num_links - num_new_links
    # if need_links > 0:
    #     log.info('We need %d links to fill feed', need_links)


    # '''
    # num links is less than max_links: we have room left over, pull in previous published..
    # num links is MORE than max_links: too many? should we cut stuff off? might get backlogged eh.. meh.
    # '''


    # #log.info('%d new links for RSS feed', num_new_links)
