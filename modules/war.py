#!/usr/bin/env python

"""NEVAR FORGET"""

import urllib, urllib2, cookielib
import re
from include import utils
from include import rssparser

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['MatchObject']
__agent__ = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'

class Terror(object):
    __url__ = 'http://www.dhs.gov/dhspublic/getAdvisoryCondition'
    __re_level__ = re.compile(r'<THREAT_ADVISORY CONDITION="(\w+)" />')
    __color_map__ = {
        'severe': 5,
        'high': 4,
        'elevated': 8,
        'guarded': 12,
        'low': 9,
    }

    def __init__(self, ua=None):
        self.ua = ua

    def level(self):
        try:
            doc = self.ua.fetch(Terror.__url__)
            level = Terror.__re_level__.search(doc).group(1)
            color = Terror.__color_map__[level.lower()]
            return '\x03%s,1\x16\x16%s\x0f' % (color, level)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return 'UNKNOWN'


class DoomsDay(object):
    __url__ = 'http://www.thebulletin.org/minutes-to-midnight/'
    __re_time__ = re.compile(r'href="/minutes-to-midnight/">(.*?)</a>')

    def __init__(self, ua=None):
        self.ua = ua

    def time(self):
        try:
            doc = self.ua.fetch(DoomsDay.__url__)
            time = DoomsDay.__re_time__.search(doc).group(1)
            return time
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return 'UNKNOWN'


class IranWar(object):
    __url__ = 'http://www.areweatwarwithiran.com/rss.xml'

    def war(self):
        try:
            rss = rssparser.parse(IranWar.__url__)
            return rss['items'].pop(0)['title']
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return 'UNKNOWN'


class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:terror|doomsday|war)\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'terror - NEVAR FORGET'
        self.ua = utils.UserAgent()
        self.terror = Terror(ua=self.ua)
        self.doom = DoomsDay(ua=self.ua)
        self.iran = IranWar()

    def response(self, **kwargs):
        try:
            return 'Terror: %s, DoomsDay: %s, IranWar: %s' % (
                    self.terror.level(), self.doom.time(), self.iran.war())
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)

if __name__ == '__main__':
    import os, sys
    print MatchObject().response(nick=os.environ['USER'])
    sys.exit(0)
