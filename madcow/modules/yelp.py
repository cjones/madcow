"""Restaraunt reviews"""

from BeautifulSoup import BeautifulSoup
from madcow.util.http import geturl
from madcow.util import Module
from learn import Main as Learn
from urlparse import urljoin
import re
from madcow.conf import settings

DEFAULT_LOCATION = 'San Francisco, CA'
BASEURL = 'http://www.yelp.com/'
SEARCHURL = urljoin(BASEURL, '/search')
RESULT_FMT = u'%(nick)s: %(name)s (%(cat)s) - %(rating)s/5 (%(reviews)s) - %(address)s [%(url)s]'
clean_re = re.compile(r'^\s*\d+\.\s*(.+?)\s*$')

class Main(Module):

    pattern = re.compile(r'^\s*yelp\s+(.+?)(?:\s+@(.+))?\s*$', re.I)
    help = 'yelp <name> [@location] - restaraunt reviews'

    def init(self):
        try:
            self.default_location = settings.YELP_DEFAULT_LOCATION
        except:
            self.default_location = DEFAULT_LOCATION
        try:
            self.learn = Learn(madcow=self.madcow)
        except:
            self.learn = None

    def response(self, nick, args, kwargs):
        # sanity check args and pick default search location
        desc, loc = args
        if desc.startswith('@') and not loc:
            raise Exception('invalid search')
        if not loc:
            if self.learn:
                loc = self.learn.lookup(u'location', nick)
            if not loc:
                loc = self.default_location

        # perform search
        opts = opts={'find_desc': desc, 'ns': 1, 'find_loc': loc, 'rpp': 1}
        page = geturl(SEARCHURL, opts)

        # extract meaningful data from first result
        soup = BeautifulSoup(page, convertEntities='html')
        result = soup.body.find('div', 'businessresult clearfix')
        name = result.find('a', id='bizTitleLink0').findAll(text=True)
        name = clean_re.search(u''.join(name)).group(1)
        cat = result.find('div', 'itemcategories').a.renderContents()
        rating = result.find('div', 'rating').img['alt']
        rating = rating.replace(' star rating', '')
        reviews = result.find('a', 'reviews')
        url = urljoin(BASEURL, reviews['href'])
        reviews = reviews.renderContents()
        address = [i.strip() for i in result.address.findAll(text=True)]
        address = u', '.join(part for part in address if part)

        # return rendered page
        return RESULT_FMT % {'nick': nick, 'name': name, 'cat': cat,
                             'rating': rating, 'reviews': reviews,
                             'address': address, 'url': url}
