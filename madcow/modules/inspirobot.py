#!/usr/bin/env python

"""Interface for getting really stupid IRC quotes"""

import re
import requests
from madcow.util import Module, strip_html


class Main(Module):

    pattern = re.compile(u'^\s*(inspire|inspirobot)(?:\s+(\S+))?', re.I)
    require_addressing = True
    help = u'inspire - get inspirational image'
    url  = 'http://inspirobot.me/api?generate=true'
    error = u':('

    def response(self, nick, args, kwargs):
        r = requests.get(url)
        if r.ok:
          return r.content
