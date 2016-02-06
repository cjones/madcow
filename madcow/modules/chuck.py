"""Get a random joke"""

from madcow.util import Module
from madcow.util.http import geturl
import re
import json


class Main(Module):

    pattern = re.compile(r'^\s*chuck(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True
    help = (u'Chuck Norris won\'t help you')
    baseurl = u'http://api.icndb.com/jokes/random'

    def response(self, nick, args, kwargs):
        doc = json.loads(geturl(self.baseurl))
        return doc['value']['joke'].replace('&quot', "'")
