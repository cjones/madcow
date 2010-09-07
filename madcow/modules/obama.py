"""Countdown to Obamanation"""

from madcow.util import Module
import re
import time

class Main(Module):

    pattern = re.compile(r'^\s*obama\s*$', re.I)
    oday = 1232470800  # jan 20, 2009 @ 9am
    units = [(u'second', 60),
             (u'minute', 60),
             (u'hour', 24),
             (u'day', 7),
             (u'week', 4),
             (u'month', 12),
             (u'year', 0)]
    help = u'obama - get precise time since we got a rid of bush'

    def response(self, nick, args, kwargs):
        e = time.time() - self.oday
        ms = int((e - int(e)) * 1000)
        return u'%s: Bush has been gone: %s %dms' % (nick, self.human_readable(e), ms)

    @classmethod
    def human_readable(cls, n):
        units = []
        for name, size in cls.units:
            n = int(n)
            if size and n >= size:
                r = n % size
                n = n / size
            else:
                r = n
                n = 0
            if r:
                if r > 1:
                    name += u's'
                units.append(u'%s %s' % (r, name))
            if not n:
                break
        if units:
            units.reverse()
            return u' '.join(units)
