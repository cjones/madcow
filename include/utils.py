#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Some helper functions"""

from __future__ import with_statement
import re
import sys
from time import time as unix_time
import os

__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = [u'Debug', u'Module', u'cache', u'throttle', u'stripHTML',
           u'unescape_entities', u'slurp', u'Request', u'cache_property']

# pre-compile regex
pre_re = re.compile(r'(<pre.*?>(.*?)</pre>)', re.I | re.DOTALL)
break_re = re.compile(r'<br.*?>', re.I | re.DOTALL)
tag_re = re.compile(r'<.*?>', re.DOTALL)
newlines_re = re.compile(r'[\r\n]+')
entity_re = re.compile(r'(&([^;]+);)')
charentity_re = re.compile(r'^&#(x)?(\d+);$', re.I)

striplines = lambda x: map(lambda item: item.strip(), newlines_re.split(x))

# entity map
entities = {u'quot': 34, u'amp': 38, u'apos': 39, u'lt': 60, u'gt': 62,
            u'nbsp': 32, u'iexcl': 161, u'cent': 162, u'pound': 163,
            u'curren': 164, u'yen': 165, u'brvbar': 166, u'sect': 167,
            u'uml': 168, u'copy': 169, u'ordf': 170, u'laquo': 171,
            u'not': 172, u'shy': 173, u'reg': 174, u'macr': 175,
            u'deg': 176, u'plusmn': 177, u'sup2': 178, u'sup3': 179,
            u'acute': 180, u'micro': 181, u'para': 182, u'middot': 183,
            u'cedil': 184, u'sup1': 185, u'ordm': 186, u'raquo': 187,
            u'frac14': 188, u'frac12': 189, u'frac34': 190, u'iquest': 191,
            u'Agrave': 192, u'Aacute': 193, u'Acirc': 194, u'Atilde': 195,
            u'Auml': 196, u'Aring': 197, u'AElig': 198, u'Ccedil': 199,
            u'Egrave': 200, u'Eacute': 201, u'Ecirc': 202, u'Euml': 203,
            u'Igrave': 204, u'Iacute': 205, u'Icirc': 206, u'Iuml': 207,
            u'ETH': 208, u'Ntilde': 209, u'Ograve': 210, u'Oacute': 211,
            u'Ocirc': 212, u'Otilde': 213, u'Ouml': 214, u'times': 215,
            u'Oslash': 216, u'Ugrave': 217, u'Uacute': 218, u'Ucirc': 219,
            u'Uuml': 220, u'Yacute': 221, u'THORN': 222, u'szlig': 223,
            u'agrave': 224, u'aacute': 225, u'acirc': 226, u'atilde': 227,
            u'auml': 228, u'aring': 229, u'aelig': 230, u'ccedil': 231,
            u'egrave': 232, u'eacute': 233, u'ecirc': 234, u'euml': 235,
            u'igrave': 236, u'iacute': 237, u'icirc': 238, u'iuml': 239,
            u'eth': 240, u'ntilde': 241, u'ograve': 242, u'oacute': 243,
            u'ocirc': 244, u'otilde': 245, u'ouml': 246, u'divide': 247,
            u'oslash': 248, u'ugrave': 249, u'uacute': 250, u'ucirc': 251,
            u'uuml': 252, u'yacute': 253, u'thorn': 254, u'yuml': 255,
            u'OElig': 338, u'oelig': 339, u'Scaron': 352, u'scaron': 353,
            u'Yuml': 376, u'circ': 710, u'tilde': 732, u'ensp': 8194,
            u'emsp': 8195, u'thinsp': 8201, u'zwnj': 8204, u'zwj': 8205,
            u'lrm': 8206, u'rlm': 8207, u'ndash': 8211, u'mdash': 8212,
            u'lsquo': 8216, u'rsquo': 8217, u'sbquo': 8218, u'ldquo': 8220,
            u'rdquo': 8221, u'bdquo': 8222, u'dagger': 8224,
            u'Dagger': 8225, u'hellip': 8230, u'permil': 8240,
            u'lsaquo': 8249, u'rsaquo': 8250, u'euro': 8364, u'trade': 8482}


class Debug(object):

    """Extra debugging base class"""

    def __repr__(self):
        return u'<%s object at 0x%x: %s>' % (self.__class__.__name__, id(self),
                                             self.__dict__)


class Module(object):

    """Base module class"""

    _any = re.compile(r'^(.+)$')
    pattern = re.compile(u'')
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
        return u'not implemented'


class Request(object):

    """Generic object passed in from protocol handlers for processing"""

    def __init__(self, message):
        self.message = message
        self.sendto = None
        self.private = False
        self.nick = None
        self.matched = False
        self.feedback = False
        self.correction = False
        self.colorize = False
        self.channel = None
        self.addressed = False


def cache_property(timeout=None):

    """Caching property decorator"""

    cache = {}

    def decorator(method):

        def inner(*args, **kwargs):
            if method in cache:
                if unix_time() - cache[method][u'lastrun'] > timeout:
                    del cache[method]
            if method not in cache:
                cache[method] = dict(lastrun=unix_time(),
                                     result=method(*args, **kwargs))
            return cache[method][u'result']

        inner.__doc__ = method.__doc__
        inner.__name__ = method.__name__
        return property(inner)
    return decorator


class cache(object):

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
                if (now - item[u'created']) > self.timeout:
                    del self.cached[key]

            # run wrapped function if there is no cached data
            if args not in self.cached:
                value = function(*args, **kwargs)
                self.cached[args] = {u'created': now, u'value': value}

            # return
            return self.cached[args][u'value']

        return callback


class throttle(object):

    """Decorator for throttling requests to prevent abuse/spamming"""

    # defaults
    _threshold = 1
    _period = 60
    _key = u'global'

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
        self.state[u'count'] = 0
        self.state[u'first_event'] = unix_time()

    def __call__(self, function):

        def callback(*args, **kwargs):
            r = repr(self.__state)
            if (unix_time() - self.state[u'first_event']) > self.period:
                self._reset()
            if self.state[u'count'] >= self.threshold:
                return
            self.state[u'count'] += 1
            return function(*args, **kwargs)

        return callback


def stripHTML(data):
    """Removes HTML cruft"""
    parts = pre_re.split(data)
    formatted = []
    while parts:
        part = parts.pop(0)
        if pre_re.match(part):
            part = break_re.sub('\n', parts.pop(0))
        else:
            part = ('\n'.join(striplines(break_re.sub(
                    '\n', ' '.join(striplines(part))))))
        part = tag_re.sub('', part)
        part = unescape_entities(part)
        formatted.append(part)
    data = '\n'.join(formatted)
    return data


def unescape_entities(text):
    for entity, name in entity_re.findall(text):
        if name in entities:
            val = entities[name]
        else:
            try:
                ishex, val = charentity_re.search(entity).groups()
            except AttributeError:
                log.warn(u"couldn't decode entity: %s" % entity)
                continue
            base = 16 if ishex else 10
            val = int(val, base)
        text = text.replace(entity, unichr(val))
    return text


def slurp(path):
    with open(path, u'rb') as file:
        return file.read()


def test_module(mod):
    main = mod()
    try:
        args = main.pattern.search(u' '.join(sys.argv[1:])).groups()
    except:
        print u'no match, double-check regex'
        return 1
    print main.response(nick=os.environ[u'USER'], args=args, kwargs={})
    return 0

