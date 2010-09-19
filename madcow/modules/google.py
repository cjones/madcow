"""I'm feeling lucky"""

from madcow.util import Module
import re
from madcow.util.google import Google

class Main(Module):

    pattern = re.compile(u'^\s*google\s+(.*?)\s*$')
    require_addressing = True
    help = u"google <query> - i'm feeling lucky"
    error = u'not so lucky today..'

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        query = args[0]
        return u'%s: %s = %s' % (nick, query, self.google.lucky(query))
