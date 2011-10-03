"""Generate RSS2"""

from urlparse import urlparse
from datetime import datetime

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

from lxml import etree
from gruntle.memebot.utils.text import encode, decode, sdecode, cast
from gruntle.memebot.utils import blacklist, local_to_gmt

__version__ = '0.1'

DEFAULT_ENCODING = 'utf-8'
DEFAULT_XML_DECLARATION = True
DEFAULT_PRETTY_PRINT = True
DEFAULT_LANGUAGE = 'en-us'  # http://cyber.law.harvard.edu/rss/languages.html
DEFAULT_DOCS = 'http://cyber.law.harvard.edu/rss/rss.html'
DEFAULT_GENERATOR = 'memebot v' + __version__

NOT_IMPLEMENTED = 'cloud', 'rating', 'text_input', 'skip_hours', 'skip_days'
ITEM_NOT_IMPLEMENTED = 'enclosure', 'source'
VALID_SCHEMES = 'http', 'https'

class XMLBuilder(object):

    def __init__(self, *args, **kwargs):
        self.stack = [self.make_element(*args, **kwargs)]

    @property
    def root(self):
        if self.stack:
            return self.stack[0]

    @property
    def current(self):
        if self.stack:
            return self.stack[-1]

    def add(self, *args, **kwargs):
        element = self.make_element(*args, **kwargs)
        self.current.append(element)
        return element

    def node(self, *args, **kwargs):
        iter = kwargs.pop('iter', None)

        class NodeContext(object):

            def __enter__(node):
                element = self.add(*args, **kwargs)
                self.stack.append(element)
                return element

            def __exit__(node, *exc_info):
                self.stack.pop()

            def __iter__(node):
                for item in iter:
                    yield item

        return NodeContext()

    def make_element(self, name, text=None, **attrib):
        attrib = ((encode(key), sdecode(val)) for key, val in attrib.iteritems())
        attrib = dict((key, val) for key, val in attrib if val is not None)
        element = etree.Element(name, attrib)
        element.text = sdecode(text)
        return element

    @property
    def tree(self):
        return etree.ElementTree(self.root)


class RSS2(list):

    weekdays = 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'
    months = 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'

    def __init__(self, link, title=None, description=None, language=None, copyright=None,
                 managing_editor=None, webmaster=None, publish_date=None, build_date=None,
                 categories=None, generator=None, docs=None, cloud=None, ttl=None, image=None,
                 rating=None, text_input=None, skip_hours=None, skip_days=None, items=None):
        if link is None:
            raise TypeError('link cannot be empty')
        url = urlparse(link)
        if url.scheme not in VALID_SCHEMES:
            raise ValueError('unsupported scheme: %r' % url.scheme)
        host = decode(blacklist.normalize(url.netloc))
        domain = '.'.join(host.split('.')[-2:])
        if title is None:
            title = link
        if description is None:
            description = title
        if language is None:
            language = DEFAULT_LANGUAGE
        if webmaster is None:
            webmaster = 'webmaster@' + domain
        now_gmt = local_to_gmt(datetime.now())
        if publish_date is None:
            publish_date = now_gmt
        if build_date is None:
            build_date = now_gmt
        if generator is None:
            generator = DEFAULT_GENERATOR
        if docs is None:
            docs = DEFAULT_DOCS
        if ttl is not None:
            ttl = cast(ttl)
            if not isinstance(ttl, (int, long)):
                raise TypeError('ttl must be an integer')
        if image is not None:
            if not isinstance(image, Image):
                image = Image(**image)
        context = locals()
        for key in NOT_IMPLEMENTED:
            if context[key] is not None:
                raise NotImplementedError('%s is not implemented' % key)

        self.link = link
        self.title = title
        self.description = description
        self.language = language
        self.copyright = copyright
        self.managing_editor = managing_editor
        self.webmaster = webmaster
        self.publish_date = publish_date
        self.build_date = build_date
        self.categories = categories
        self.generator = generator
        self.docs = docs
        self.ttl = ttl
        self.image = image

    def add_item(self, *args, **kwargs):
        self.append(RSS2Item(*args, **kwargs))

    @property
    def tree(self):
        xml = XMLBuilder('rss', version='2.0')
        with xml.node('channel'):
            xml.add('link', self.link)
            xml.add('title', self.title)
            xml.add('description', self.description)
            xml.add('language', self.language)
            xml.add('copyright', self.copyright)
            xml.add('managingEditor', self.managing_editor)
            xml.add('webMaster', self.webmaster)
            xml.add('pubData', self.format_date(self.publish_date))
            xml.add('lastBuildDate', self.format_date(self.build_date))
            for category, domain in self.parse_categories(self.categories):
                xml.add('category', category, domain=domain)
            xml.add('generator', self.generator)
            xml.add('docs', self.docs)
            xml.add('ttl', self.ttl)

            with xml.node('image'):
                if self.image is not None:
                    xml.add('url', self.image.url)
                    xml.add('title', self.image.title or self.title)
                    xml.add('link', self.image.link or self.link)
                    xml.add('width', self.image.width)
                    xml.add('height', self.image.height)

            for item in self:
                with xml.node('item'):
                    xml.add('link', item.link)
                    xml.add('title', item.title)
                    xml.add('description', item.description)
                    xml.add('author', item.author)
                    for category, domain in self.parse_categories(item.categories):
                        xml.add('category', category, domain=domain)
                    xml.add('comments', item.comments)
                    xml.add('guid', item.guid)
                    publish_date = self.publish_date if item.publish_date is None else item.publish_date
                    xml.add('pubDate', self.format_date(publish_date))
                    #xml.add('enclosure', item.enclosure)
                    #xml.add('source', item.source)

        return xml.tree

    @classmethod
    def format_date(cls, dt):
        if dt is not None:
            return '%s, %02d %s %04d %02d:%02d:%02d GMT' % (
                    cls.weekdays[dt.weekday()], dt.day, cls.months[dt.month - 1],
                    dt.year, dt.hour, dt.minute, dt.second)

    @staticmethod
    def parse_categories(categories):
        if categories is not None:
            for category in categories:
                if category is None or isinstance(category, (str, unicode)):
                    domain = None
                elif isinstance(category, (tuple, list)):
                    nfields = len(category)
                    if nfields == 1:
                        category, domain = category[0], None
                    elif nfields == 2:
                        category, domain = category
                    else:
                        raise ValueError('invalid category fields')
                else:
                    raise TypeError('invalid category')
                yield category, domain

    def write(self, *args, **kwargs):
        kwargs.setdefault('encoding', DEFAULT_ENCODING)
        kwargs.setdefault('xml_declaration', DEFAULT_XML_DECLARATION)
        kwargs.setdefault('pretty_print', DEFAULT_PRETTY_PRINT)
        self.tree.write(*args, **kwargs)

    def tostring(self, *args, **kwargs):
        fp = stringio.StringIO()
        self.write(fp, *args, **kwargs)
        return fp.getvalue()


class RSS2Item(object):

    def __init__(self,
                 link,
                 title=None,
                 description=None,
                 author=None,
                 categories=None,
                 comments=None,
                 enclosure=None,
                 guid=None,
                 publish_date=None,
                 source=None):

        if link is None:
            raise TypeError('link cannot be empty')
        url = urlparse(link)
        if url.scheme not in VALID_SCHEMES:
            raise ValueError('unsupported scheme: %r' % url.scheme)
        if title is None:
            title = link
        if description is None:
            description = title
        if guid is None:
            guid = link
        context = locals()
        for key in ITEM_NOT_IMPLEMENTED:
            if context[key] is not None:
                raise NotImplementedError('%s is not implemented' % key)

        self.link = link
        self.title = title
        self.description = description
        self.author = author
        self.categories = categories
        self.comments = comments
        self.guid = guid
        self.publish_date = publish_date
        #self.enclosure = enclosure
        #self.source = source


class Image(object):

    def __init__(self, url, title=None, link=None, width=None, height=None):
        self.url = url
        self.title = title
        self.link = link
        self.width = width
        self.height = height
