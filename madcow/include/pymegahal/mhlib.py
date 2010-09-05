"""Interface to Megahal Brain"""

from struct import Struct
import sys
import os

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

COOKIE = 'MegaHALv8'

class Open(object):

    def __init__(self, file, mode='rb'):
        self.file = file
        self.mode = mode
        self.fp = None
        self.external = None
        self.pos = None

    def __enter__(self):
        if isinstance(self.file, basestring):
            self.fp = open(self.file, self.mode)
            self.external = False
        elif isinstance(self.file, (int, long)):
            self.fp = os.fdopen(self.file, self.mode)
            self.external = True
        elif hasattr(self.file, 'seek'):
            self.fp = self.file
            self.external = True
        else:
            raise TypeError('file must be a path, descriptor, or fileobj')
        if self.external:
            self.pos = self.fp.tell()
        return self.fp

    def __exit__(self, *exc_info):
        if self.external:
            self.fp.seek(self.pos, os.SEEK_SET)


class Megahal(object):

    order_fmt = Struct('B')
    tree_fmt = Struct('<HLHH')
    words_fmt = Struct('<L')
    size_fmt = Struct('B')

    def __init__(self, file):
        with Open(file, 'rb') as fp:
            self.fp = fp
            self.decode()

    def dump(self, file=None):
        if file is None:
            file = StringIO()
        with Open(file, 'wb') as fp:
            self.encode(fp)
        if not fp.closed:
            return fp

    def dumps(self):
        return self.dump().getvalue()

    def decode(self):
        if self.fp.read(len(COOKIE)) != COOKIE:
            raise IOError('not a megahal brain')
        self.order = self.unpack(self.order_fmt)
        self.forward = self.loadtree()
        self.backward = self.loadtree()
        self.words = [self.fp.read(self.unpack(self.size_fmt))
                      for _ in xrange(self.unpack(self.words_fmt))]

    def encode(self, fp):
        fp.write(COOKIE)
        fp.write(self.order_fmt.pack(self.order))
        self.dumptree(fp, self.forward)
        self.dumptree(fp, self.backward)
        fp.write(self.words_fmt.pack(len(self.words)))
        for word in self.words:
            fp.write(self.size_fmt.pack(len(word)))
            fp.write(word)

    def loadtree(self):
        node = list(self.unpack(self.tree_fmt))
        node.append([self.loadtree() for _ in xrange(node[3])])
        return node

    def dumptree(self, fp, node):
        fp.write(self.tree_fmt.pack(*node[:4]))
        for child in node[4]:
            self.dumptree(fp, child)

    def unpack(self, fmt):
        result = fmt.unpack(self.fp.read(fmt.size))
        if len(result) == 1:
            return result[0]
        return result
