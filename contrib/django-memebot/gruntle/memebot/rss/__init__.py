"""RSS generation"""

from urlparse import urljoin
import datetime
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from gruntle.memebot.rss.generator import RSS2, RSS2Item
from gruntle.memebot.models import SerializedData, Link
from gruntle.memebot.decorators import logged, locked
from gruntle.memebot.utils import AtomicWrite, first, local_to_gmt, plural, text

DEFAULT_MAX_LINKS = 100

current_site = Site.objects.get_current()

class LinkItem(RSS2Item):

    """A single Link feed item"""

    def __init__(self, link):
        super(LinkItem, self).__init__(
                first(link.resolved_url, link.url),
                title=link.title,
                description='<b>Coming Soon</b>',
                author=link.user.username,
                guid=link.guid,
                publish_date=local_to_gmt(link.published))


class LinkFeed(RSS2):

    """A feed generator for Link objects"""

    def __init__(self, links, feed):
        now = local_to_gmt(datetime.datetime.now())
        super(LinkFeed, self).__init__(
                urljoin(feed.base_url, reverse('index')),
                title=feed.title,
                description=feed.description,
                language=feed.language,
                copyright=feed.copyright,
                webmaster=feed.webmaster,
                ttl=feed.ttl,
                image=feed.image,
                publish_date=now,
                build_date=now)

        for link in links:
            self.append(LinkItem(link))


class Feed(object):

    """Base Feed class"""

    base_url = settings.FEED_BASE_URL
    title = None
    description = None
    language = settings.LANGUAGE_CODE
    copyright = settings.FEED_COPYRIGHT
    webmaster = settings.FEED_WEBMASTER
    ttl = settings.FEED_TTL
    image = settings.FEED_IMAGE_URL

    def generate(self, published_links, max_links=None, log=None, name=None, feed_dir=None):
        if max_links is None:
            max_links = self.max_links
            if max_links is None:
                max_links = DEFAULT_MAX_LINKS
        if feed_dir is None:
            feed_dir = settings.FEED_DIR

        links = self.filter(published_links)[:max_links]
        if not links.count():
            log.warn('No links left to publish after filtering')
            return

        last_publish_id = SerializedData.data[name]
        if last_publish_id is None:
            last_publish_id = 0
        log.info('Last publish ID: %d', last_publish_id)

        latest_link = links[0]
        log.info('Latest publish ID: %d', latest_link.publish_id)

        if last_publish_id >= latest_link.publish_id:
            log.warn('No new links posted, not rebuilding')
            return

        log.info('Generating RSS ...')
        link_feed = LinkFeed(links, self)

        xml = link_feed.tostring()
        xml_file = os.path.join(feed_dir, name.replace('.', '-') + '.rss')

        with AtomicWrite(xml_file, backup=True, perms=0644) as fp:
            fp.write(xml)

        log.info('Wrote %d bytes to feed: %r', len(xml), xml_file)

    def filter(self, published_links):
        raise NotImplementedError


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
def rebuild_rss(logger, max_links=None):
    """Rebuild all RSS feeds"""
    feeds = get_feeds(settings.FEEDS)
    logger.info('Rebuilding %s', plural(len(feeds), 'RSS feed'))

    published_links = Link.objects.filter(state='published').order_by('-published')
    new_links = Link.objects.filter(state='new')
    invalid_links = Link.objects.filter(state='invalid')

    logger.info('%s, %s, %s',
                plural(published_links.count(), 'published link'),
                plural(new_links.count(), 'new link'),
                plural(invalid_links.count(), 'invalid link'))

    for feed_name, feed in feeds:
        log = logger.get_named_logger(feed_name)
        log.info('Rebuilding: %s', first(feed.title, feed.description, feed_name))
        feed.generate(published_links, max_links=max_links, log=log, name=feed_name)
