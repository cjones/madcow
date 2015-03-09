"""I'm feeling lucky"""

from madcow.util import Module
import re
from madcow.util.google import Google

class Main(Module):

    pattern = re.compile(r'^(?:search|g(?:oog(?:le)?)?)\s+(.+)\s*$', re.I)
    require_addressing = True
    help = u"(g[oog[le]]|search) <query> - i'm feeling lucky"
    error = u'not so lucky today..'

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        query = args[0]
        return u'{}: {}'.format(nick, self.google.lucky(query))
