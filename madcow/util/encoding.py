#!/usr/bin/env python

import sys
import re
import codecs
import chardet

DEFAULT = u'ascii'
meta_re = re.compile(r'<meta\s+(.*?)\s*>', re.I | re.DOTALL)
attr_re = re.compile(r'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*(\'[^\']*\'|"[^"'
                     r']*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~@]*))?')

def convert(data, headers=None):
    """Return unicode object of data"""
    if isinstance(data, str):
        data = data.decode(detect(data, headers), u'replace')
    return data


def detect(data, headers=None):
    """Return charset of data"""
    from madcow.util import get_logger
    log = get_logger()

    # try to figure out the encoding first from meta tags
    charset = metacharset(data)
    if charset:
        log.debug(u'using http meta header encoding: %s' % charset)
        return charset

    # if that doesnu't work, see if there's a real http header
    if headers and headers.plist:
        charset = headers.plist[0]
        attrs = parseattrs(charset)
        if u'charset' in attrs:
            charset = lookup(attrs[u'charset'])
        if charset:
            log.debug(u'using http header encoding: %s' % charset)
            return charset

    # that didn't work, try chardet library
    charset = lookup(chardet.detect(data)[u'encoding'])
    if charset:
        log.debug(u'detected encoding: %s' % repr(charset))
        return charset

    # if that managed to fail, just use ascii
    log.warn(u"couldn't detect encoding, using ascii")
    return DEFAULT


def lookup(charset):
    """Lookup codec"""
    try:
        return codecs.lookup(charset).name
    except (LookupError, TypeError, AttributeError):
        pass


def metacharset(data):
    """Parse data for HTML meta character encoding"""
    for meta in meta_re.findall(data):
        attrs = parseattrs(meta)
        if (u'http-equiv' in attrs and
            attrs[u'http-equiv'].lower() == u'content-type' and
            u'content' in attrs):
            content = attrs[u'content']
            content = parseattrs(content)
            if u'charset' in content:
                return lookup(content[u'charset'])


def parseattrs(data):
    """Parse key=val attributes"""
    #log.warn('PARSEATTRS: %r' % data)
    attrs = {}
    for key, rest, val in attr_re.findall(data):
        if not rest:
            val = None
        elif val[:1] == '\'' == val[-1:] or val[:1] == '"' == val[-1:]:
            val = val[1:-1]
        attrs[key.lower()] = val
    return attrs


def get_encoding():
    for encoding in sys.getfilesystemencoding(), sys.getdefaultencoding(), 'ascii':
        try:
            return codecs.lookup(encoding).name
        except LookupError:
            pass
    else:
        raise

ENCODING = get_encoding()
