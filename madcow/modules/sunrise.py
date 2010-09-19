"""Get sunrise or sunset from google"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.color import ColorLib
from learn import Main as Learn
from google import Google

class Main(Module):

    pattern = re.compile(r'^\s*(sunrise|sunset)(?:\s+(@?)(.+?))?\s*$', re.I)
    help = '(sunrise|sunset) [location|@nick] - get time of sun rise/set'
    error = u"That place doesn't have a sun, sorry"

    def init(self):
        self.colorlib = self.madcow.colorlib
        try:
            self.learn = Learn(madcow=madcow)
        except:
            self.learn = None
        self.google = Google()

    def response(self, nick, args, kwargs):
        query, args = args[0], args[1:]
        if not args[1]:
            args = 1, nick
        if args[0]:
            location = self.learn.lookup('location', args[1])
            if not location:
                return u'%s: Try: set location <nick> <location>' % nick
        else:
            location = args[1]
        response = self.google.sunrise_sunset(query, location)
        return u'%s: %s' % (nick, response)
