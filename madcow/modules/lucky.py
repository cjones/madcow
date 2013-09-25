"""I'm feeling lucky"""

from madcow.util import Module
import re
from madcow.util.google import Google

GOOGLE = '\x1b[m\x0f\x1b[1m\x1b[34mG\x1b[31mo\x1b[33mo\x1b[34mg\x1b[32ml\x1b[31me\x1b[m\x0f'


class Main(Module):

    pattern = re.compile(r'^(?:search|lucky?)\s+(.+)\s*$', re.I)
    require_addressing = True
    help = u"(g[oog[le]]|search) <query> - i'm feeling lucky"
    error = u'not so lucky today..'

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        query = args[0]

        return u'{}: {}: {}'.format(nick, GOOGLE, self.google.lucky(query))
