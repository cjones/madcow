"""Feed generation core"""

from urlparse import urljoin
import datetime
import os

from django.conf import settings
from django.core.urlresolvers import reverse

from gruntle.memebot.models import SerializedData, Link
from gruntle.memebot.decorators import logged, locked
from gruntle.memebot.utils import AtomicWrite, first, plural, text, rss

class LinkItem(rss.Item):

    """A single Link feed item"""

    def __init__(self, link):
        super(LinkItem, self).__init__(link.best_url,
                                       title=link.get_title_display(),
                                       desc=link.rendered,
                                       author=link.user.username,
                                       guid=link.guid,
                                       published=link.published)


class RSSFeed(rss.RSS):

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


class BaseFeed(object):

    """Defines the interface and defaults for a content feed"""

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

    def __init__(self, name, published_links, logger):
        self.name = name
        self.published_links = published_links
        self.log = logger.get_named_logger(name)
        self._links = None

    @property
    def xml_file(self):
        """Location of file output"""
        return os.path.join(self.feed_dir, self.name + '.xml')

    @property
    def image(self):
        """An Image object if an image_url is defined for this feed"""
        if self.image_url is not None:
            return rss.Image(url=self.image_url,
                             title=self.image_title,
                             link=self.image_link,
                             width=self.image_width,
                             height=self.image_height)

    @property
    def stylesheets(self):
        """A list of StyleSheet objects if a stylesheet is defined for this feed"""
        if self.stylesheet is not None:
            return [rss.StyleSheet(type='text/css', media='screen', href=self.stylesheet)]

    @property
    def links(self):
        """Links valid for this feed"""
        if self._links is None:
            links = self.filter(self.published_links)
            if self.max_links:
                links = links[:self.max_links]
            self._links = links
        return self._links

    @property
    def key(self):
        """Our key in SerializedData"""
        return self.name + '_last_published'

    @property
    def newest_publish_id(self):
        if self.links.count():
            return self.links[0].publish_id

    @property
    def last_publish_id(self):
        last = SerializedData.data[self.key]
        if last is None:
            last = 0
        return last

    @property
    def has_new_links(self):
        """True if there are newly published links that have not been exported"""
        return self.last_publish_id < self.newest_publish_id

    def reverse(self, view, *args, **kwargs):
        """Reverse look up a URL, fully qualified by base_url"""
        return urljoin(self.base_url, reverse(view, args=args, kwargs=kwargs))

    def generate(self, force=False, **kwargs):
        """Generate the feed"""
        link_count = self.links.count()
        if link_count:
            if force or self.has_new_links:
                self.log.info('Rebuilding feed with %d items', link_count)
                xml = RSSFeed(self).tostring(**kwargs)
                with AtomicWrite(self.xml_file, backup=self.keep_xml_backup, perms=0644) as fp:
                    fp.write(xml)
                self.log.info('Wrote %d bytes to: %s', len(xml), self.xml_file)
                SerializedData.data[self.key] = self.newest_publish_id
            else:
                self.log.info('No new links to publish')
        else:
            self.log.warn('No links valid for this feed')

    def filter(self, published_links):
        """Override by subclasses to control what links get exported to the feed"""
        return published_links


def get_feeds():
    """Import the feed models defined in settings.FEEDS"""
    return [(path.rsplit('.', 1)[1], __import__(path, globals(), locals(), ['Feed']).Feed) for path in settings.FEEDS]


def get_feed_names():
    """Get just the name of the feeds"""
    return [name for name, cls in get_feeds()]


@logged('feeds', append=True)
@locked('feeds', 0)
def run(logger, force=False):
    """Rebuild all feeds"""
    feeds = get_feeds()
    logger.info('Rebuilding %s', plural(len(feeds), 'feed'))
    published_links = Link.objects.filter(state='published').order_by('-published')
    for name, cls in feeds:
        feed = cls(name, published_links, logger)
        feed.generate(encoding=settings.FEED_ENCODING, force=force)
