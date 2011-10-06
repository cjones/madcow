"""XML helper tools"""

import contextlib
import re

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

from lxml import etree
from gruntle.memebot.utils import text

DEFAULT_XML_DECLARATION = True
DEFAULT_PRETTY_PRINT = True
DEFAULT_ENCODING = 'utf-8'

class TreeBuilder(object):

    """Helper to build XML tree more declaratively than lxml.etree normally allows for"""

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
    def current(self):
        """Currently active node"""
        if self.stack:
            return self.stack[-1]

    @property
    def tree(self):
        """Root tree"""
        return self.root.getroottree()

    @contextlib.contextmanager
    def child(self, *args, **kwargs):
        """Add a child node and append new tags to it until this context is left"""
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

    def write(self, *args, **kwargs):
        """Write rendered element tree"""
        kwargs.setdefault('xml_declaration', DEFAULT_XML_DECLARATION)
        kwargs.setdefault('pretty_print', DEFAULT_PRETTY_PRINT)
        kwargs.setdefault('encoding', DEFAULT_ENCODING)
        self.tree.write(*args, **kwargs)

    def tostring(self, *args, **kwargs):
        """Return RSS element tree as string"""
        fp = stringio.StringIO()
        self.write(fp, *args, **kwargs)
        return fp.getvalue()
