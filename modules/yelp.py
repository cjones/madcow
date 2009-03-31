#!/usr/bin/env python
#
# Copyright (C) 2007-2009 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Restaraunt reviews"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from include.utils import stripHTML
from include.BeautifulSoup import BeautifulSoup
from urlparse import urljoin

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

DEFAULT_LOCATION = 'San Francisco, CA'

class Main(Module):

    base_url = 'http://www.yelp.com/'
    search_url = urljoin(base_url, '/search')
    pattern = re.compile(r'^\s*yelp\s+(.+?)(?:\s+@(.+))?\s*$', re.I)
    help = 'yelp <name> [@location] - restaraunt reviews'
    result_attrs = {'class': re.compile(r'businessresult')}
    name_attrs = {'class': 'highlighted'}
    cat_attrs = {'class': 'itemcategories'}
    rating_attrs = {'class': 'rating'}
    review_attrs = {'class': 'reviews'}
    phone_attrs = {'class': 'phone'}
    result_fmt = (u'%(nick)s: %(name)s (%(cat)s) - %(rating)s/5 (%(reviews)s)'
                  u' - %(address)s [%(url)s]')

    def __init__(self, madcow=None):
        try:
            self.default_location = madcow.config.yelp.default_location
        except:
            self.default_location = DEFAULT_LOCATION

    def response(self, nick, args, kwargs):
        try:
            desc, loc = args
            if not loc:
                loc = self.default_location
            opts = opts={'find_desc': desc, 'ns': 1, 'find_loc': loc, 'rpp': 1}
            page = geturl(self.search_url, opts=opts)
            soup = BeautifulSoup(page)
            result = soup.find('div', attrs=self.result_attrs)
            name = result.find('span', attrs=self.name_attrs)
            name = u''.join(name.contents).strip()
            cat = result.find('div', attrs=self.cat_attrs).find('a')
            cat = u''.join(cat.contents).strip()
            rating = result.find('div', attrs=self.rating_attrs).find('img')
            rating = rating['alt'].strip().replace(' star rating', '')
            reviews = result.find('a', attrs=self.review_attrs)
            url = urljoin(self.base_url, reviews['href'])
            reviews = u''.join(reviews.contents).strip()
            address = result.find('address')
            address = [part.strip() for part in address.contents
                       if isinstance(part, unicode)]
            phone = result.find('div', attrs=self.phone_attrs)
            phone = u''.join(phone.contents).strip()
            address.append(phone)
            address = u', '.join(part for part in address if part)
            result = self.result_fmt % {'nick': nick, 'name': name, 'cat': cat,
                                        'rating': rating, 'reviews': reviews,
                                        'address': address, 'url': url}
            return stripHTML(result)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: I couldn't look that up" % nick


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
