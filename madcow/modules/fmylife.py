"""Get a random confession from fmylife.com"""

from madcow.util import Module, strip_html
from madcow.util.http import getsoup
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
        soup = getsoup(self.spec_url % int(args[0]) if args[0] else self.rand_url)
        soup.find('div', id='submit').extract()
        post = soup.body.find('div', 'post')
        id = int(post.find('a', 'fmllink')['href'].split('/')[-1])
        body = strip_html(decode(' '.join(link.renderContents() for link in post('a', 'fmllink')), 'utf-8'))
        return u'%s: (%d) %s' % (nick, id, body)
