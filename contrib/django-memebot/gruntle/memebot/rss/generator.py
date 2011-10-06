"""RSS 2.0 generator that uses lxml"""

from contextlib import contextmanager
from datetime import datetime
import re

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

from lxml import etree

from gruntle.memebot.utils import text, rfc822time, iso8061time

__version__ = '0.1'

class DOMBuilder(object):

    """Helper to build XML tree more declaratively than etree normally allows for"""

    attrib_text_re = re.compile(r'<\s*(.+?)(?:\s+(.+?))?\s*/\s*>', re.DOTALL)

    def __init__(self, *args, **kwargs):
        self.add_empty_tags = kwargs.pop('add_empty_tags', False)
        kwargs.setdefault('resolve_ns', False)
        self.stack = [self.make_element(*args, **kwargs)]

    @property
    def root(self):
        """Root element"""
        if self.stack:
            return self.stack[0]

    @property
    def tree(self):
        """Root tree"""
        return self.root.getroottree()

    @property
    def current(self):
        """Currently active node"""
        if self.stack:
            return self.stack[-1]

    @contextmanager
    def node(self, *args, **kwargs):
        """Descend a level while in context"""
        try:
            element = self.make_element(*args, **kwargs)
            self.current.append(element)
            self.stack.append(element)
            yield element
        finally:
            self.stack.pop()

    def add(self, *args, **kwargs):
        """Created element and add to current node"""
        element = self.make_element(*args, **kwargs)
        if self.add_empty_tags or element.text or element.attrib:
            self.current.append(element)
            return element

    def add_pi(self, name, **attrib):
        """Add a ProcessingInstruction"""
        text = self.attrib_text_re.search(etree.tostring(self.make_element('Fake', **attrib), encoding=unicode))
        if text is not None:
            text = text.group(2)
        self.root.addprevious(etree.PI(name, text))

    def make_element(self, name, val=None, **attrib):
        """Created an element from params"""
        val = text.sdecode(val)
        if attrib.pop('cdata', False) and val:
            val = etree.CDATA(val)
        nsmap = attrib.pop('nsmap', None)
        resolve_ns = attrib.pop('resolve_ns', True)
        attrib = dict(i for i in (map(text.sdecode, i) for i in attrib.iteritems()) if None not in i)
        if resolve_ns:
            ns, _, tag = name.rpartition(':')
            ns = self.root.nsmap.get(ns)
            if ns:
                tag = '{%s}%s' % (ns, tag)
        else:
            tag = name
        element = etree.Element(tag, attrib, nsmap)
        element.text = val
        return element


class RSS(list):

    """Represents an RSS feed"""

    def __init__(self, link, title=None, desc=None, language=None, copyright=None, self_link=None,
                 managing_editor=None, webmaster=None, published=None, build_date=None,
                 categories=None, generator=None, docs=None, ttl=None, image=None, stylesheets=None):
        self.link = link
        self.title = title or self.link
        self.desc = desc or self.title
        self.language = language or 'en-us'
        self.copyright = copyright
        self.self_link = self_link
        self.managing_editor = managing_editor
        self.webmaster = webmaster
        self.published = published or datetime.now()
        self.build_date = build_date or self.published
        self.categories = categories
        self.generator = generator or 'MemeBot RSS Generator v%s' % (__version__,)
        self.docs = docs or 'http://cyber.law.harvard.edu/rss/rss.html'
        self.ttl = ttl
        self.image = image
        self.stylesheets = stylesheets

    def add_item(self, *args, **kwargs):
        """Add a new item to the channel"""
        self.append(Item(*args, **kwargs))

    @property
    def tree(self):
        """Rendered ElementTree of the RSS"""
        dom = DOMBuilder('rss', version='2.0', nsmap={'dc': 'http://purl.org/dc/elements/1.1/',
                                                      'atom': 'http://www.w3.org/2005/Atom',
                                                      'gruntle': 'http://gruntle.org/xmlns/gruntle/1.0/'})

        with dom.node('channel'):
            dom.add('link', self.link)
            dom.add('title', self.title)
            dom.add('description', self.desc)
            dom.add('language', self.language)
            dom.add('copyright', self.copyright)
            dom.add('managingEditor', self.managing_editor)
            dom.add('webMaster', self.webmaster)
            dom.add('pubDate', rfc822time(self.published))
            dom.add('lastBuildDate', rfc822time(self.build_date))
            dom.add('generator', self.generator)
            dom.add('docs', self.docs)
            dom.add('ttl', self.ttl)

            for category, domain in self.parse_categories(self.categories):
                dom.add('category', category, domain=domain)

            if self.image is not None:
                with dom.node('image'):
                    dom.add('url', self.image.url)
                    dom.add('title', self.image.title or self.title)
                    dom.add('link', self.image.link or self.link)
                    dom.add('width', self.image.width)
                    dom.add('height', self.image.height)

            if self.self_link:
                dom.add('atom:link', rel='self', type='application/rss+xml', href=self.self_link)

            for item in self:
                published = item.published or self.published
                with dom.node('item'):
                    dom.add('link', item.link)
                    dom.add('title', item.title)
                    dom.add('description', item.desc)
                    dom.add('author', item.author)
                    dom.add('comments', item.comments)
                    dom.add('guid', item.guid, isPermaLink='false')
                    dom.add('pubDate', rfc822time(published))

                    for category, domain in self.parse_categories(item.categories):
                        dom.add('category', category, domain=domain)

                    # Atom extensions
                    dom.add('atom:content', item.desc, type='html')

                    # Dublin Core extensions
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
                dom.add_pi('xml-stylesheet', **stylesheet.attrib)

        return dom.tree

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

    def write(self, *args, **kwargs):
        """Write rendered RSS element tree"""
        kwargs.setdefault('xml_declaration', True)
        kwargs.setdefault('pretty_print', True)
        kwargs.setdefault('encoding', 'utf-8')
        self.tree.write(*args, **kwargs)

    def tostring(self, *args, **kwargs):
        """Return RSS element tree as string"""
        fp = stringio.StringIO()
        self.write(fp, *args, **kwargs)
        return fp.getvalue()


class Item(object):

    """Represents a single RSS item"""

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

    """Represents an RSS Image"""

    def __init__(self, url, title=None, link=None, width=None, height=None):
        self.url = url
        self.title = title
        self.link = link
        self.width = width
        self.height = height


class StyleSheet(object):

    """Container for stylesheet PI attributes"""

    def __init__(self, **attrib):
        self.attrib = attrib
