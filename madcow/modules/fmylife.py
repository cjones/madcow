"""Get a random confession from fmylife.com"""

from madcow.util import Module, strip_html
from madcow.util.text import *
from urlparse import urljoin
import re

class Main(Module):

    pattern = re.compile(u'^\s*fml\s*(\d+)?\s*$', re.I)
    require_addressing = True
    help = u'fml - misery from fmylife.com'
    base_url = 'http://www.fmylife.com/'
    rand_url = urljoin(base_url, 'random')
    spec_url = urljoin(base_url, '%d')
    error = u'Today I couldn\'t seem to access fmylife.com.. FML'

    def response(self, nick, args, kwargs):
        soup = self.getsoup(self.spec_url % int(args[0]) if args[0] else self.rand_url)
        entry = soup.body('a', 'fmllink')[0]
        id = int(entry['href'].split('/')[-1])
        body = strip_html(decode(entry.renderContents()))
        return u'%s: (%d) %s' % (nick, id, body)
