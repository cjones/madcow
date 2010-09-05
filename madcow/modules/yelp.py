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

from BeautifulSoup import BeautifulSoup
from madcow.util.http import geturl
from madcow.util import Module
from learn import Main as Learn
from urlparse import urljoin
import logging as log
import re

__version__ = '0.2'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

DEFAULT_LOCATION = 'San Francisco, CA'
BASEURL = 'http://www.yelp.com/'
SEARCHURL = urljoin(BASEURL, '/search')
RESULT_FMT = u'%(nick)s: %(name)s (%(cat)s) - %(rating)s/5 (%(reviews)s) - %(address)s [%(url)s]'
clean_re = re.compile(r'^\s*\d+\.\s*(.+?)\s*$')

class Main(Module):

    pattern = re.compile(r'^\s*yelp\s+(.+?)(?:\s+@(.+))?\s*$', re.I)
    help = 'yelp <name> [@location] - restaraunt reviews'

    def __init__(self, madcow=None):
        try:
            self.default_location = madcow.config.yelp.default_location
        except:
            self.default_location = DEFAULT_LOCATION
        try:
            self.learn = Learn(madcow=madcow)
        except:
            self.learn = None

    def response(self, nick, args, kwargs):
        try:
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

        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: I couldn't look that up" % nick


if __name__ == u'__main__':
    from madcow.util import test_module
    test_module(Main)
