"""RSS 2.0 feed generator"""

from gruntle.memebot.utils import xml
from gruntle.memebot.utils.tzdatetime import tzdatetime

__version__ = '0.1'

NAMESPACE_RSS2 = 'http://backend.userland.com/RSS2'
NAMESPACE_ATOM = 'http://www.w3.org/2005/Atom'
NAMESPACE_DC = 'http://purl.org/dc/elements/1.1/'

DEFAULT_GENERATOR = 'MemeBot RSS Generator v' + __version__
DEFAULT_DOCS = NAMESPACE_RSS2
DEFAULT_LANGUAGE = 'en-us'

class RSS(list):

    """An RSS 2.0 feed"""

    def __init__(self, link, title=None, desc=None, language=None, copyright=None, rss_url=None,
                 editor=None, webmaster=None, published=None, build_date=None, categories=None,
                 generator=None, docs=None, ttl=None, image=None, stylesheets=None, add_atom=False,
                 add_dc=False, extra_namespaces=None):
        self.link = link
        self.title = title or self.link
        self.desc = desc or self.title
        self.language = language or DEFAULT_LANGUAGE
        self.copyright = copyright
        self.rss_url = rss_url
        self.editor = editor
        self.webmaster = webmaster
        self.published = tzdatetime.new(published)
        self.build_date = self.published if build_date is None else tzdatetime.new(build_date)
        self.categories = categories or []
        self.generator = generator or DEFAULT_GENERATOR
        self.docs = docs or DEFAULT_DOCS
        self.ttl = ttl
        self.image = image
        self.stylesheets = stylesheets or []
        self.add_atom = add_atom
        self.add_dc = add_dc
        self.extra_namespaces = extra_namespaces

    @property
    def nsmap(self):
        """Namespace map for this feed"""
        #nsmap = {None: NAMESPACE_RSS2}
        nsmap = {}
        if self.add_atom:
            nsmap['atom'] = NAMESPACE_ATOM
        if self.add_dc:
            nsmap['dc'] = NAMESPACE_DC
        if self.extra_namespaces is not None:
            nsmap.update(self.extra_namespaces)
        return nsmap

    @property
    def rss_tree(self):
        """Build the RSS tree"""
        rss = xml.TreeBuilder('rss', version='2.0', nsmap=self.nsmap)

        with rss.child('channel'):
            rss.add('link', self.link)
            rss.add('title', self.title)
            rss.add('description', self.desc)
            rss.add('language', self.language)
            rss.add('copyright', self.copyright)
            rss.add('managingEditor', self.editor)
            rss.add('webMaster', self.webmaster)
            rss.add('pubDate', self.published.rfc822format())
            rss.add('lastBuildDate', self.build_date.rfc822format())
            rss.add('generator', self.generator)
            rss.add('docs', self.docs)
            rss.add('ttl', self.ttl)

            for category in self.categories:
                rss.add('category', category.name, domain=category.domain)

            if self.image is not None:
                with rss.child('image'):
                    rss.add('url', self.image.url)
                    rss.add('title', self.image.title or self.title)
                    rss.add('link', self.image.link or self.link)
                    rss.add('width', self.image.width)
                    rss.add('height', self.image.height)

            if self.add_atom and self.rss_url:
                rss.add('atom:link', rel='self', type='application/rss+xml', href=self.rss_url)

            for item in self:
                published = self.published if item.published is None else tzdatetime.new(item.published)
                with rss.child('item'):
                    rss.add('link', item.link)
                    rss.add('title', item.title)
                    rss.add('description', item.desc)
                    rss.add('author', item.author)
                    rss.add('comments', item.comments)
                    rss.add('guid', item.guid, isPermaLink='false')
                    rss.add('pubDate', published.rfc822format())

                    for category in item.categories:
                        rss.add('category', category.name, domain=category.domain)

                    if self.add_dc:
                        rss.add('dc:title', item.title)
                        rss.add('dc:creator', item.author)
                        rss.add('dc:language', self.language)
                        rss.add('dc:rights', self.copyright)
                        rss.add('dc:date', published.isoformat())
                        rss.add('dc:format', item.content_type)
                        rss.add('dc:identifier', item.guid)

        for stylesheet in self.stylesheets:
            rss.add_pi('xml-stylesheet', **stylesheet.__dict__)

        return rss

    def write(self, *args, **kwargs):
        """Write RSS as XML"""
        self.rss_tree.write(*args, **kwargs)

    def tostring(self, *args, **kwargs):
        """Return RSS as XML string"""
        return self.rss_tree.tostring(*args, **kwargs)


class Item(object):

    """An RSS news item"""

    def __init__(self, link, title=None, desc=None, author=None, content_type=None,
                 categories=None, comments=None, guid=None, published=None):
        self.link = link
        self.title = title or self.link
        self.desc = desc or self.title
        self.author = author
        self.content_type = content_type or 'text/html'
        self.categories = categories or []
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
