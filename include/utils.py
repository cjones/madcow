#!/usr/bin/env python

"""Some helper functions"""

import re
import urllib, urllib2, cookielib
import sys
from time import time as unix_time
import os

__version__ = '0.2'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['Base', 'Module', 'Error', 'cache', 'throttle', 'stripHTML',
        'isUTF8', 'unescape_entities', 'slurp']

re_sup = re.compile('<sup>(.*?)</sup>', re.I)
re_br = re.compile('<br[^>]+>', re.I)
re_tags = re.compile('<[^>]+>')
re_newlines = re.compile('[\r\n]+')
re_highascii = re.compile('([\x80-\xff])')
re_entity = re.compile(r'(&([^;]+);)')

entityNames = {
    'quot': 34, 'amp': 38, 'apos': 39, 'lt': 60, 'gt': 62, 'nbsp': 32,
    'iexcl': 161, 'cent': 162, 'pound': 163, 'curren': 164, 'yen': 165,
    'brvbar': 166, 'sect': 167, 'uml': 168, 'copy': 169, 'ordf': 170,
    'laquo': 171, 'not': 172, 'shy': 173, 'reg': 174, 'macr': 175, 'deg': 176,
    'plusmn': 177, 'sup2': 178, 'sup3': 179, 'acute': 180, 'micro': 181,
    'para': 182, 'middot': 183, 'cedil': 184, 'sup1': 185, 'ordm': 186,
    'raquo': 187, 'frac14': 188, 'frac12': 189, 'frac34': 190, 'iquest': 191,
    'Agrave': 192, 'Aacute': 193, 'Acirc': 194, 'Atilde': 195, 'Auml': 196,
    'Aring': 197, 'AElig': 198, 'Ccedil': 199, 'Egrave': 200, 'Eacute': 201,
    'Ecirc': 202, 'Euml': 203, 'Igrave': 204, 'Iacute': 205, 'Icirc': 206,
    'Iuml': 207, 'ETH': 208, 'Ntilde': 209, 'Ograve': 210, 'Oacute': 211,
    'Ocirc': 212, 'Otilde': 213, 'Ouml': 214, 'times': 215, 'Oslash': 216,
    'Ugrave': 217, 'Uacute': 218, 'Ucirc': 219, 'Uuml': 220, 'Yacute': 221,
    'THORN': 222, 'szlig': 223, 'agrave': 224, 'aacute': 225, 'acirc': 226,
    'atilde': 227, 'auml': 228, 'aring': 229, 'aelig': 230, 'ccedil': 231,
    'egrave': 232, 'eacute': 233, 'ecirc': 234, 'euml': 235, 'igrave': 236,
    'iacute': 237, 'icirc': 238, 'iuml': 239, 'eth': 240, 'ntilde': 241,
    'ograve': 242, 'oacute': 243, 'ocirc': 244, 'otilde': 245, 'ouml': 246,
    'divide': 247, 'oslash': 248, 'ugrave': 249, 'uacute': 250, 'ucirc': 251,
    'uuml': 252, 'yacute': 253, 'thorn': 254, 'yuml': 255, 'OElig': 338,
    'oelig': 339, 'Scaron': 352, 'scaron': 353, 'Yuml': 376, 'circ': 710,
    'tilde': 732, 'ensp': 8194, 'emsp': 8195, 'thinsp': 8201, 'zwnj': 8204,
    'zwj': 8205, 'lrm': 8206, 'rlm': 8207, 'ndash': 8211, 'mdash': 8212,
    'lsquo': 8216, 'rsquo': 8217, 'sbquo': 8218, 'ldquo': 8220, 'rdquo': 8221,
    'bdquo': 8222, 'dagger': 8224, 'Dagger': 8225, 'hellip': 8230,
    'permil': 8240, 'lsaquo': 8249, 'rsaquo': 8250, 'euro': 8364,
    'trade': 8482,
}

entityMap = {
    352: 'S', 353: 's', 376: 'Y', 710: '^', 732: '~', 8194: ' ', 8195: '  ',
    8211: '-', 8212: '--', 8216: "'", 8217: "'", 8218: "'", 8220: '"',
    8221: '"', 8222: '"', 8224: '+', 8225: '', 8230: '...', 8240: '%.',
    8249: '<', 8250: '>', 8364: '$', 8482: '(tm)',
}

class Base(object):
    """Base class"""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.__dict__.update(kwargs)

    def __str__(self):
        return '<%s %s>' % (self.__class__.__name__, repr(self.__dict__))

    __repr__ = __str__


class Module(Base):
    _any = re.compile(r'^(.+)$')
    pattern = re.compile('')
    enabled = True
    require_addressing = True
    help = None
    priority = 50
    terminate = True
    allow_threading = True
    error = None

    def __init__(self, madcow=None):
        self.madcow = madcow

    def response(self, nick, args, **kwargs):
        return 'not implemented'


class Error(Exception):
    """Base Exception class"""

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return str(self.message)

    __repr__ = __str__


class cache:
    """Decorator for caching return values"""
    _timeout = 3600

    def __init__(self, timeout=_timeout):
        self.timeout = timeout
        self.cached = {}

    def __call__(self, function):

        def callback(*args, **kwargs):
            now = unix_time()

            # expire cache values that have aged beyond timeout
            for key, item in self.cached.items():
                if (now - item['created']) > self.timeout:
                    del self.cached[key]

            # run wrapped function if there is no cached data
            if not self.cached.has_key(args):
                value = function(*args, **kwargs)
                self.cached[args] = {'created': now, 'value': value}

            # return
            return self.cached[args]['value']

        return callback


class throttle(Base):
    """Decorator for throttling requests to prevent abuse/spamming"""

    # defaults
    _threshold = 1
    _period = 60
    _key = 'global'

    # store state here, shared between instances
    __state = {}

    def __init__(self, threshold=_threshold, period=_period, key=_key):
        self.threshold = threshold
        self.period = period
        self.key = key
        self.__state.setdefault(key, {})
        self._reset()

    def get_state(self):
        return self.__state[self.key]

    state = property(get_state)

    def _reset(self):
        self.state['count'] = 0
        self.state['first_event'] = unix_time()

    def __call__(self, function):

        def callback(*args, **kwargs):
            r = repr(self.__state)
            if (unix_time() - self.state['first_event']) > self.period:
                self._reset()
            if self.state['count'] >= self.threshold:
                return
            self.state['count'] += 1
            return function(*args, **kwargs)

        return callback


def stripHTML(data=None):
    if data is None:
        return

    data = re_sup.sub(r'^\1', data)
    data = re_tags.sub('', data)
    data = re_br.sub('\n', data)
    data = re_newlines.sub('\n', data)
    data = unescape_entities(data)
    return data

def isUTF8(data = None, threshold = .25):
    if (float(len(re_highascii.findall(data))) / float(len(data))) > threshold:
        return True
    else:
        return False

def unescape_entities(text):
    for entity, entityName in re_entity.findall(text):
        if entityNames.has_key(entityName):
            val = entityNames[entityName]
        elif entityName.startswith('#') and entityName[1:].isdigit():
            val = int(entityName[1:])
        else:
            continue

        if val < 256:
            converted = chr(val)
        elif entityMap.has_key(val):
            converted = entityMap[val]
        else:
            converted = ''

        text = text.replace(entity, converted)

    return text

def slurp(filename):
    try:
        f = open(filename, 'rb')
        try:
            data = f.read()
        finally:
            f.close()
        return data
    except Exception, e:
        print >> sys.stderr, "couldn't read %s: %s" % (filename, e)

def test_module(mod):
    main = mod()
    try:
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
    except:
        print 'no match, double-check regex'
        return 1
    print main.response(nick=os.environ['USER'], args=args)
    return 0
