#!/usr/bin/env python

"""
Simple HTML parser

Works similar to BeautifulSoup but a lot, well, simpler.  The rationale
behind this library is because BeautifulSoup seems abandoned and I need
another way to do this if I want to make a 3.0-compatible Madcow.

May choke on badly formed HTML.
"""

import sys
from HTMLParser import HTMLParser as _HTMLParser
from collections import defaultdict
from UserDict import DictMixin
import re

__all__ = ['HTMLParser']

class Data(DictMixin):

    """Behave like a dict with instance variable for every key"""

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, val):
        self.__dict__[key] = val

    def __delitem__(self, key):
        del self.__dict__[key]

    def keys(self):
        return self.__dict__.keys()


class ParsedDocument(object):

    """A parsed HTML tree"""

    def __init__(self, parts, index):
        self._parts = parts
        self._index = index

    def findall(self, name=None, attrs=None, max=None):
        """Yields tuple of tag, attributes, and contents"""
        if name and name not in self._index:
            return
        count = 0
        for i, part in enumerate(self._parts):
            if part.type != 'starttag':
                continue
            if name and i not in self._index[name]:
                continue
            if attrs:
                match = True
                for key, val in attrs.items():
                    if key not in part.attrs:
                        match = False
                        break
                    if isinstance(val, basestring):
                        val = re.compile(re.escape(val))
                    if not val.search(part.attrs[key]):
                        match = False
                        break
                if not match:
                    continue
            if part.end:
                contents = ''.join(
                        x.data
                        for x in self._parts[part.start:part.end]
                        if x.type == 'data')
            else:
                contents = ''
            yield part.name, part.attrs, contents
            count += 1
            if max and count >= max:
                break

    def find(self, name, attrs=None):
        """Return first occurence of tag"""
        return self.findall(name, attrs, 1).next()

    def __getitem__(self, i):
        return self._parts[i]

    def __getslice__(self, i, j):
        return self._parts[i:j]

    def __len__(self):
        return len(self._parts)

    def __iter__(self):
        return self.findall()


class HTMLParser(_HTMLParser):

    """Simple HTML parser"""

    def __init__(self):
        _HTMLParser.__init__(self)

    def parse(self, data):
        self.parts = []
        self.index = defaultdict(list)
        self.stack = defaultdict(list)
        try:
            self.feed(data)
            result = ParsedDocument(self.parts, self.index)
            return result
        finally:
            del self.parts, self.index, self.stack

    def handle_starttag(self, name, attrs):
        tag = Data(type='starttag', name=name, attrs=Data(**dict(attrs)),
                   start=len(self.parts), end=None)
        self.index[name].append(tag.start)
        self.stack[name].insert(0, tag)
        self.parts.append(tag)

    def handle_endtag(self, name):
        if name in self.stack and self.stack[name]:
            tag = self.stack[name].pop(0)
            tag.end = len(self.parts)
        self.parts.append(Data(type='endtag', name=name))

    def handle_data(self, data):
        self.parts.append(Data(type='data', data=data))

