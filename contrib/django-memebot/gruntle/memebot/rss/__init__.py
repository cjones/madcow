"""RSS generation"""

from urlparse import urljoin
import datetime
import os

from django.conf import settings
from django.core.urlresolvers import reverse

from gruntle.memebot.rss.generator import RSS, Item, Image, StyleSheet
from gruntle.memebot.models import SerializedData, Link
from gruntle.memebot.decorators import logged, locked
from gruntle.memebot.utils import AtomicWrite, first, plural, text

class LinkItem(Item):

    """A single Link feed item"""

    def __init__(self, link):
        super(LinkItem, self).__init__(link.best_url,
                                       title=link.get_title_display(),
                                       desc=link.rendered,
                                       author=link.user.username,
                                       guid=link.guid,
                                       published=link.published)


class LinkRSS(RSS):

    """A feed generator for Link objects"""

    def __init__(self, links, feed=None, name=None):
        now = datetime.datetime.now()
        super(LinkRSS, self).__init__(urljoin(feed.base_url, reverse('memebot-view-index')),
                                      title=feed.title,
                                      desc=feed.description,
                                      language=feed.language,
                                      copyright=feed.copyright,
                                      self_link=urljoin(feed.base_url, reverse('memebot-view-rss', args=[name])),
                                      webmaster=feed.webmaster,
                                      published=now,
                                      build_date=now,
                                      ttl=feed.ttl,
                                      image=feed.image,
                                      stylesheets=feed.stylesheets)

        for link in links:
            self.append(LinkItem(link))


class Feed(object):

    """Base Feed class"""

    title = None
    description = None

    base_url = settings.FEED_BASE_URL
    language = settings.LANGUAGE_CODE
    copyright = settings.FEED_COPYRIGHT
    webmaster = settings.FEED_WEBMASTER
    ttl = settings.FEED_TTL
    max_links = settings.FEED_MAX_LINKS
    feed_dir = settings.FEED_DIR
    stylesheet = settings.FEED_STYLESHEET

    image_url = settings.FEED_IMAGE_URL
    image_title = settings.FEED_IMAGE_TITLE
    image_link = settings.FEED_IMAGE_LINK
    image_width = settings.FEED_IMAGE_WIDTH
    image_height = settings.FEED_IMAGE_HEIGHT

    @property
    def image(self):
        if self.image_url is not None:
            return Image(url=self.image_url,
                         title=self.image_title,
                         link=self.image_link,
                         width=self.image_width,
                         height=self.image_height)

    @property
    def stylesheets(self):
        if self.stylesheet is not None:
            return [StyleSheet(type='text/css', media='screen', href=self.stylesheet)]

    def generate(self, published_links, max_links=None, log=None, name=None, feed_dir=None, force=False):
        if max_links is None:
            max_links = self.max_links
        if feed_dir is None:
            feed_dir = self.feed_dir

        links = self.filter(published_links)
        if max_links:
            links = links[:max_links]
        if not links.count():
            log.warn('No links left to publish after filtering')
            return

        last_publish_key = name + '_last_published'
        last_publish_id = SerializedData.data[last_publish_key]
        if last_publish_id is None:
            last_publish_id = 0
        log.info('Last publish ID: %d', last_publish_id)

        latest_link = links[0]
        log.info('Latest publish ID: %d', latest_link.publish_id)

        if last_publish_id >= latest_link.publish_id:
            if force:
                log.warn('No new links posted, but forcing regeneration anyway')
            else:
                log.info('No new links posted')
                return

        log.info('Generating RSS ...')
        rss = LinkRSS(links, feed=self, name=name)
        xml = rss.tostring()
        xml_file = os.path.join(feed_dir, name + '.rss')

        with AtomicWrite(xml_file, backup=True, perms=0644) as fp:
            fp.write(xml)

        log.info('Wrote %d bytes to feed: %r', len(xml), xml_file)
        SerializedData.data[last_publish_key] = latest_link.publish_id
        log.info('Updated %s to: %r', last_publish_key, SerializedData.data[last_publish_key])

    def filter(self, published_links):
        raise NotImplementedError


def get_feeds(paths=None):
    """Import configured feeds"""
    if paths is None:
        paths = settings.FEEDS
    func_name = 'feed'
    global_context = globals()
    local_context = locals()
    feeds = []
    for path in paths:
        mod = __import__(path, global_context, local_context, [func_name])
        feed = getattr(mod, func_name, None)
        if feed is not None:
            feeds.append((path.split('.')[-1], path, feed))
    return feeds


def get_feed_names(paths=None):
    if paths is None:
        paths = settings.FEEDS
    return [name for name, path, feed in get_feeds(paths)]


@logged('build-rss', append=True)
@locked('build-rss', 0)
def rebuild_rss(logger, max_links=None, force=False):
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

    for feed_name, feed_path, feed in feeds:
        log = logger.get_named_logger(feed_name)
        log.info('Rebuilding: %s', first(feed.title, feed.description, feed_name))
        feed.generate(published_links, max_links=max_links, log=log, name=feed_name, force=force)
