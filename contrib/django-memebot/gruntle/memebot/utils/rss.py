"""RSS 2.0 generator that uses lxml"""

from datetime import datetime
from gruntle.memebot.utils import xml, rfc822time, iso8061time

__version__ = '0.1'

DEFAULT_GENERATOR = 'MemeBot RSS Generator v' + __version__
DEFAULT_DOCS = 'http://cyber.law.harvard.edu/rss/rss.html'
DEFAULT_LANGUAGE = 'en-us'

NAMESPACE_ATOM = 'http://www.w3.org/2005/Atom'
NAMESPACE_DC = 'http://purl.org/dc/elements/1.1/'

class RSS(list):

    """An RSS 2.0 feed"""

    def __init__(self, link, title=None, desc=None, language=None, copyright=None, rss_url=None,
                 editor=None, webmaster=None, published=None, build_date=None, categories=None,
                 generator=None, docs=None, ttl=None, image=None, stylesheets=None, add_atom=False, add_dc=False):
        self.link = link
        self.title = title or self.link
        self.desc = desc or self.title
        self.language = language or DEFAULT_LANGUAGE
        self.copyright = copyright
        self.rss_url = rss_url
        self.editor = editor
        self.webmaster = webmaster
        self.published = published or datetime.now()
        self.build_date = build_date or self.published
        self.categories = categories
        self.generator = generator or DEFAULT_GENERATOR
        self.docs = docs or DEFAULT_DOCS
        self.ttl = ttl
        self.image = image
        self.stylesheets = stylesheets
        self.add_atom = add_atom
        self.add_dc = add_dc

    def add_item(self, *args, **kwargs):
        """Add a new item to the channel"""
        self.append(Item(*args, **kwargs))

    @property
    def dom(self):
        """The complete DOM"""
        nsmap = {}
        if self.add_atom:
            nsmap['atom'] = NAMESPACE_ATOM
        if self.add_dc:
            nsmap['dc'] = NAMESPACE_DC
        dom = xml.TreeBuilder('rss', version='2.0', nsmap=nsmap)

        with dom.child('channel'):
            dom.add('link', self.link)
            dom.add('title', self.title)
            dom.add('description', self.desc)
            dom.add('language', self.language)
            dom.add('copyright', self.copyright)
            dom.add('managingEditor', self.editor)
            dom.add('webMaster', self.webmaster)
            dom.add('pubDate', rfc822time(self.published))
            dom.add('lastBuildDate', rfc822time(self.build_date))
            dom.add('generator', self.generator)
            dom.add('docs', self.docs)
            dom.add('ttl', self.ttl)

            for name, domain in self.categories:
                dom.add('category', name, domain=domain)

            if self.image is not None:
                with dom.child('image'):
                    dom.add('url', self.image.url)
                    dom.add('title', self.image.title or self.title)
                    dom.add('link', self.image.link or self.link)
                    dom.add('width', self.image.width)
                    dom.add('height', self.image.height)

            if self.add_atom and self.rss_url:
                dom.add('atom:link', rel='self', type='application/rss+xml', href=self.rss_url)

            for item in self:
                published = item.published or self.published
                with dom.child('item'):
                    dom.add('link', item.link)
                    dom.add('title', item.title)
                    dom.add('description', item.desc)
                    dom.add('author', item.author)
                    dom.add('comments', item.comments)
                    dom.add('guid', item.guid, isPermaLink='false')
                    dom.add('pubDate', rfc822time(published))

                    for category, nodeain in self.parse_categories(item.categories):
                        dom.add('category', category, nodeain=nodeain)

                    # Dublin Core extensions
                    if self.add_dc:
                        dom.add('dc:title', item.title)
                        dom.add('dc:creator', item.author)
                        dom.add('dc:contributor', item.author)
                        dom.add('dc:publisher', item.author)
                        dom.add('dc:format', item.content_type)
                        dom.add('dc:identifier', item.guid)
                        dom.add('dc:language', self.language)
                        dom.add('dc:rights', self.copyright)
                        dom.add('dc:date', iso8061time(published))

        if self.stylesheets is not None:
            for stylesheet in self.stylesheets:
                dom.add_pi('xml-stylesheet', **stylesheet.__dict__)

    def write(self, *args, **kwargs):
        """Write RSS as XML"""

        dom.tree.write(*args, **kwargs)

    @staticmethod
    def parse_categories(categories):
        """Parse categories and yield category, domain tuples"""
        if categories is not None:
            for category in categories:
                if isinstance(category, (str, unicode)):
                    domain = None
                else:
                    category, domain = category
                yield category, domain


class Item(object):

    """An RSS news item"""

    def __init__(self, link, title=None, desc=None, author=None, content_type=None,
                 categories=None, comments=None, guid=None, published=None):
        self.link = link
        self.title = title or self.link
        self.desc = desc or self.title
        self.author = author
        self.content_type = content_type or 'text/html'
        self.categories = categories
        self.comments = comments
        self.guid = guid or self.link
        self.published = published


class Image(object):

    """A channel image"""

    def __init__(self, url, title=None, link=None, width=None, height=None):
        self.url = url
        self.title = title
        self.link = link
        self.width = width
        self.height = height


class StyleSheet(object):

    """An xml-stylesheet Processing Instruction"""

    def __init__(self, href, type='text/css', media='screen'):
        self.href = href
        self.type = type
        self.media = media


class Category(object):

    """A category node"""

    def __init__(self, name, domain=None):
        self.name = name
        self.domain = domain
