"""Mystery meat demistifier: Scrape youtube titles"""

from madcow.util.http import getsoup
from madcow.util.text import decode
from madcow.util import Module, strip_html
from urlparse import urlparse

import cgi
import re
import os

LOGO = u'\x1b[m\x0f\x1b[30m\x1b[47mYou\x1b[37m\x1b[41m\x1b[1mTube\x1b[m\x0f'
SCHEMES = frozenset({'http', 'https'})
DOMAINS = frozenset({'youtube.com'})

class Main(Module):

    pattern = re.compile(r'(https?://(?:\w+\.)?youtube\.com/\S+)', re.I)
    require_addressing = False
    priority = 90
    allow_threading = True
    terminate = False

    def __init__(self, bot):
        self.bot = bot

    def response(self, nick, args, kwargs):
        try:
            url = args[0]
            uri = urlparse(url)
            if (uri.scheme.lower() in SCHEMES and
                    '.'.join(uri.netloc.lower().split('.')[-2:]) in DOMAINS and
                    os.path.split(os.path.normpath(uri.path))[-1] == 'watch' and
                    'v' in cgi.parse_qs(uri.query)):
                soup = getsoup(url)
                title = strip_html(decode(soup.title.renderContents())).replace(u' - YouTube', u'').strip()
                if title:
                    response = u'{}: {}'.format(LOGO, title)
                    self.bot.output(response, kwargs['req'])
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
