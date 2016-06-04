"""Look up drink mixing ingredients"""

import re
from madcow.util import Module, strip_html
from urlparse import urljoin

class Main(Module):

    pattern = re.compile(u'^\s*drinks?\s+(.+)', re.I)
    require_addressing = True
    help = u'drinks <drink name> - look up mixing instructions'
    baseurl = u'http://www.webtender.com/'
    search = urljoin(baseurl, u'/cgi-bin/search')
    drink = re.compile(u'<A HREF="(/db/drink/\d+)">')
    title = re.compile(u'<H1>(.*?)<HR></H1>')
    ingredients = re.compile(u'<LI>(.*?CLASS=ingr.+)')
    instructions = re.compile(u'<H3>Mixing instructions:</H3>.*?<P>(.*?)</P>', re.DOTALL)
    error = u"Something ungood happened looking that up, sry"

    def response(self, nick, args, kwargs):
        try:
            query = args[0]
            doc = self.geturl(self.search, opts={u'verbose': u'on', u'name': query})
            drink = self.drink.search(doc).group(1)
            url = urljoin(self.baseurl, drink)
            doc = self.geturl(url)
            title = self.title.search(doc).group(1)
            ingredients = self.ingredients.findall(doc)
            instructions = self.instructions.search(doc).group(1)
            response = strip_html(u'%s - %s - %s' % (title, u', '.join(ingredients), instructions))
        except Exception, error:
            response = u"That's a made-up drink, sorry."
        return u'%s: %s' % (nick, response)
