#!/usr/bin/env python

"""This module looks up area codes and returns the most likely city"""

import re
from madcow.util import Module
from madcow.util.http import getsoup
from madcow.util.text import *

render = lambda node: decode(node.renderContents(), 'utf-8').strip()
proper = lambda name: ' '.join(word.capitalize() for word in name.split())

class Main(Module):

    pattern = re.compile(u'^\s*area(?:\s+code)?\s+(\d+)\s*', re.I)
    require_addressing = True
    help = u'area <areacode> - what city does it belong to'
    url = 'http://www.melissadata.com/lookups/ZipCityPhone.asp'
    error = u"I couldn't look that up for some reason.  D:"

    def response(self, nick, args, kwargs):
        soup = getsoup(self.url, {'InData': args[0]})
        city = soup.body.find('table', bgcolor='#ffffcc').a
        return u'%s: %s: %s, %s' % (
                nick, args[0], proper(render(city).capitalize()),
                proper(render(city.parent.findNext('td'))))
