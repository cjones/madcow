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


class RSSFeed(RSS):

    """A feed generator for Link objects"""

    def __init__(self, feed):
        super(RSSFeed, self).__init__(feed.reverse('memebot-view-index'),
                                      title=feed.title,
                                      desc=feed.description,
                                      language=feed.language,
                                      copyright=feed.copyright,
                                      rss_url=feed.reverse('memebot-view-rss', feed.name),
                                      webmaster=feed.webmaster,
                                      ttl=feed.ttl,
                                      image=feed.image,
                                      stylesheets=feed.stylesheets,
                                      add_atom=True,
                                      add_dc=True)

        for link in feed.links:
            self.append(LinkItem(link))


class Feed(object):

    """Base Feed"""

    # you must set these on the subclass
    title = None
    description = None

    # the rest of these attributes can be overridden, these are just defaults
    base_url = settings.FEED_BASE_URL
    language = settings.LANGUAGE_CODE
    copyright = settings.FEED_COPYRIGHT
    webmaster = settings.FEED_WEBMASTER
    ttl = settings.FEED_TTL
    max_links = settings.FEED_MAX_LINKS
    feed_dir = settings.FEED_DIR
    stylesheet = settings.FEED_STYLESHEET
    keep_xml_backup = settings.FEED_KEEP_XML_BACKUP

    image_url = settings.FEED_IMAGE_URL
    image_title = settings.FEED_IMAGE_TITLE
    image_link = settings.FEED_IMAGE_LINK
    image_width = settings.FEED_IMAGE_WIDTH
    image_height = settings.FEED_IMAGE_HEIGHT

    def __init__(self):
        self.name = os.path.splitext(os.path.basename(__file__))[0]

    @property
    def xml_file(self):
        """Location of file output"""
        return os.path.join(self.feed_dir, self.name + '.xml')

    @property
    def image(self):
        """An Image object if an image_url is defined for this feed"""
        if self.image_url is not None:
            return Image(url=self.image_url,
                         title=self.image_title,
                         link=self.image_link,
                         width=self.image_width,
                         height=self.image_height)

    @property
    def stylesheets(self):
        """A list of StyleSheet objects if a stylesheet is defined for this feed"""
        if self.stylesheet is not None:
            return [StyleSheet(type='text/css', media='screen', href=self.stylesheet)]

    def reverse(self, view, *args, **kwargs):
        """Reverse look up a URL, fully qualified by base_url"""
        return urljoin(self.base_url, reverse(view, args=args, kwargs=kwargs)),

    def generate(self, published_links, log, force=False, **kwargs):
        """Generate the feed"""
        links = self.filter(published_links)
        if self.max_links:
            links = links[:self.max_links]
        if not links.count():
            log.warn('No links left to publish after filtering')
            return

        last_publish_key = self.name + '_last_published'
        last_publish_id = SerializedData.data[last_publish_key]
        if last_publish_id is None:
            last_publish_id = 0
        log.info('Last publish ID: %d', last_publish_id)

        latest_link = links[0]
        log.info('Latest publish ID: %d', latest_link.publish_id)

        if force or last_publish_id < latest_link.publish_id:
            xml = RSSFeed(feed, links).tostring(**kwargs)
            with AtomicWrite(self.xml_file, backup=self.keep_xml_backup, perms=0644) as fp:
                fp.write(xml)
            log.info('Wrote %d bytes to feed: %r', len(xml), self.xml_file)
            SerializedData.data[last_publish_key] = latest_link.publish_id

    def filter(self, published_links):
        """Override by subclasses to control what links get exported to the feed"""
        return published_links


def get_feeds():
    """Import configured feeds"""
    return [__import__(path, globals(), locals(), []).feed for path in settings.FEEDS]


def get_feed_names():
    """Get just the name of the feeds"""
    return [feed.name for feed in get_feeds]


@logged('rss', append=True)
@locked('rss', 0)
def run(logger, force=False):
    """Rebuild all RSS feeds"""
    feeds = get_feeds(settings.FEEDS)
    logger.info('Rebuilding %s', plural(len(feeds), 'RSS feed'))
    links = Link.objects.filter(state='published').order_by('-published')
    for feed in feeds:
        log = logger.get_named_logger(feed.name)
        log.info('Rebuilding: %s', first(feed.title, feed.description, feed.name))

        feed.generate(published_links, log=log, force=force)
