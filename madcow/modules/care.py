#!/usr/bin/env python

"""High Precision Care-O-Meter"""

from madcow.util import Module
import re
from google import Google

class Main(Module):

    pattern = re.compile(r'^\s*care(?:(?:[- ]?o)?[- ]?meter)?\s+(.+)\s*$', re.I)
    help = u'care <#> - display a care-o-meter'
    error = u'invalid care factor'
    isnum = re.compile(r'^\s*[0-9.]+\s*$')
    sep = re.compile(r'\s*=\s*')
    numsep = re.compile(r'(\d)\s+(\d)')
    title = u'CARE-O-METER'

    # settings
    size = 40
    min = 0
    max = 100

    def init(self):
        self.google = Google()
        self.bar = [i for i in u'.' * self.size]
        self.size = float(self.size)
        self.min = float(self.min)
        self.max = float(self.max)
        self.range = self.max - self.min

    def response(self, nick, args, kwargs):
        val = args[0]
        if not self.isnum.search(val):
            # try google calculator if not a number
            val = self.google.calculator(val)
            val = self.numsep.sub(r'\1\2', val)
            val = self.sep.split(val)[1]
            val = val.split()[0]
        val = float(val)

        # sanity check value
        if val < self.min:
            val = self.min
        elif val > self.max:
            val = self.max

        # create bar
        pos = int(round((self.size - 1) * ((val - self.min) / self.range)))
        bar = list(self.bar)
        bar[pos] = u'o'
        bar = u''.join(bar)
        bar = u'|' + bar + u'|'
        return u'%s: %s' % (self.title, bar)
