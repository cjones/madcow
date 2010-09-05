"""Predicted Electoral Vote Count"""

import re
from madcow.util.http import geturl
from madcow.util.color import ColorLib
from madcow.util import Module

class Main(Module):

    pattern = re.compile(r'^\s*(election|ev)\s*$', re.I)
    help = u'ev - current election 2008 vote prediction'
    _baseurl = u'http://www.electoral-vote.com/'
    _score_re = re.compile(r'<td class="score">(.*?)</td>', re.DOTALL)
    _dem_re = re.compile(r'<span class="dem">(.*?)\s+(\d+)')
    _gop_re = re.compile(r'<span class="gop">(.*?)\s+(\d+)')
    _tie_re = re.compile(r'(Ties)\s+(\d+)')

    def init(self):
        if self.madcow is None:
            self.colorlib = ColorLib('ansi')
        else:
            self.colorlib = self.madcow.colorlib

    def colorize(self, color, key, val):
        if key == '_SEN!D':
            key = 'Democrats'
        elif key == '_SEN!R':
            key = 'Republicans'
        key = self.colorlib.get_color(color, text=key)
        return u'%s: %s' % (key, val)

    def response(self, nick, args, kwargs):
        page = geturl(self._baseurl)
        try:
            score = self._score_re.search(page).group(1)
            dem = self._dem_re.search(score).groups()
            gop = self._gop_re.search(score).groups()
            # XXX diebold patch :D
            #dem, gop = (dem[0], gop[1]), (gop[0], dem[1])
            tie = None
            try:
                tie = self._tie_re.search(score).groups()
            except AttributeError:
                pass
        except AttributeError:
            raise Exception(u"couldn't parse page")
        output = [self.colorize(u'blue', *dem), self.colorize(u'red', *gop)]
        if tie:
            output.append(self.colorize(u'white', *tie))
        return u'%s: Projected Senate Seats 2010: %s' % (nick, u', '.join(output))
