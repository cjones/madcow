"""The real Youtube search"""

from madcow.util.http import getsoup
from madcow.util.text import decode
from madcow.util import Module, strip_html
from urlparse import urlparse
from madcow.util.google import Google

import cgi
import re
import os

SCHEMES = frozenset({'http', 'https'})
DOMAINS = frozenset({'youtube.com'})

YOUTUBE = 'Youtube'


class Main(Module):

    pattern = re.compile(r'^(?:search|youtube?)\s+(.+)\s*$', re.I)
    require_addressing = True
    help = u"(youtube) <query> - Uses google to guess first video match then parses the title"
    error = u'not so lucky today..'

    priority = 90
    allow_threading = True
    terminate = False

    def __init__(self, bot):
        self.google = Google()
        self.bot = bot

    def response(self, nick, args, kwargs):
        query = 'site\:youtube.com/watch '+args[0]
        #return u'{}: {}: {}'.format(nick, YOUTUBE, self.google.lucky(query))

        url = self.google.lucky(query)
        uri = urlparse(url)
        if (uri.scheme.lower() in SCHEMES and
                '.'.join(uri.netloc.lower().split('.')[-2:]) in DOMAINS and
                os.path.split(os.path.normpath(uri.path))[-1] == 'watch' and
                'v' in cgi.parse_qs(uri.query)):
            soup = getsoup(url)
            title = strip_html(decode(soup.title.renderContents())).replace(u' - YouTube', u'').strip()
            if title:
                response = u'{} - {}'.format(title, url)
                self.bot.output(response, kwargs['req'])
            else:
                return u'{} - {}'.format('Cant find youtube link, here is a google lucky search', url)
