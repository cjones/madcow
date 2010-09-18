#!/usr/bin/env python

"""High Precision Care-O-Meter"""

from madcow.util import Module
import re
from google import Google

class Main(Module):

    pattern = re.compile(r'^\s*(care|dongs|boner)\s+(.+?)\s*$', re.I)
    help = '\n'.join([
        u'care <#> - display a care-o-meter',
        u'dongs <#> - like care, but more penile'])
    error = u'invalid care factor'
    isnum = re.compile(r'^\s*[0-9.]+\s*$')
    sep = re.compile(r'\s*=\s*')
    numsep = re.compile(r'(\d)\s+(\d)')
    title = u'CARE-O-METER'

    # settings
    size = 40
    min = 0
    max = 100
    maxboner = 3 * 400

    def init(self):
        self.google = Google()
        self.bar = [i for i in u'.' * self.size]
        self.size = float(self.size)
        self.min = float(self.min)
        self.max = float(self.max)
        self.range = self.max - self.min

    def response(self, nick, args, kwargs):
        command, val = args
        iscare = command == 'care'
        if not self.isnum.search(val):
            # try google calculator if not a number
            try:
                val = self.google.calculator(val)
                val = self.numsep.sub(r'\1\2', val)
                val = self.sep.split(val)[1]
                val = val.split()[0]
            except:
                return u"%s: what is this i don't even"
        val = float(val)

        # sanity check value
        if val < self.min:
            val = self.min
        elif val > self.max:
            if iscare:
                val = self.max
            else:
                val = self.maxboner

        pos = int(round((self.size - 1) * ((val - self.min) / self.range)))
        if command == 'care':
            bar = list(self.bar)
            bar[pos] = u'o'
            bar = u''.join(bar)
            bar = u'|' + bar + u'|'
            bar = u'%s: %s' % (self.title, bar)
        else:
            bar = u'8' + '=' * pos + 'e'
        return bar
