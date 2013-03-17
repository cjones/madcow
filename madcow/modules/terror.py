"""NEVAR FORGET"""

import re
import feedparser
from madcow.util import Module, strip_html
from madcow.util.http import geturl
from madcow.util.color import ColorLib
from madcow.util.text import *

FORMAT = u'DoomsDay: %s, BodyCount: %s'

class DoomsDay(object):

    _url = u'http://www.thebulletin.org/'
    _re_time = re.compile(r'<div class="module-content"><h3>(.*?)</h3>')

    def time(self):
        try:
            doc = geturl(DoomsDay._url)
            time = self._re_time.search(doc).group(1)
            return time
        except Exception, error:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
            return u'UNKNOWN'


class IraqWar(object):

    _bodycount_url = u'http://www.iraqbodycount.org/database/'
    _re_whitespace = re.compile(r'\s+')
    _bodycount_re = re.compile(r"<p class='ibc-range'>(.*?)</p>", re.DOTALL)

    def bodycount(self):

        try:
            doc = geturl(self._bodycount_url)
            data = self._bodycount_re.search(doc).group(1)
            data = decode(data, 'ascii')
            data = strip_html(data)
            data = self._re_whitespace.sub(u' ', data)
            data = data.strip()
            return data
        except Exception, error:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
            return u'UNKNOWN'


class Main(Module):

    pattern = re.compile(u'^\s*(?:terror|doomsday|war)\s*$', re.I)
    require_addressing = True
    help = u'terror - NEVAR FORGET'

    def init(self):
        colorlib = self.madcow.colorlib
        self.doom = DoomsDay()
        self.iraq = IraqWar()

    def response(self, nick, args, kwargs):
        return FORMAT % (self.doom.time(), self.iraq.bodycount())
