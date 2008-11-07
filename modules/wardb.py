#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Lookup Warhammer Online items"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from include.utils import stripHTML
from urlparse import urljoin
from include.colorlib import ColorLib

__version__ = u'0.1'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = Module._any
    require_addressing = False
    help = u'[item] - look up warhammer item stats'
    priority = 5
    terminate = False

    _base_url = u'http://www.wardb.com/'
    _search_url = urljoin(_base_url, u'/search.aspx')
    _items_re = re.compile(r'\[([^\]]+)\]')
    _results_re = re.compile(
            r'<a href="([^"]+/item\.aspx[^"]+)">\s*(.+?)\s*</a>')
    _redirect_re = re.compile(
            r'self\.location="(item.aspx[^"]+)"')
    _bonus_re = re.compile(
            r"<span class='item-tooltip-bonus'>\s*([^<]+)\s*</span>")
    _stat_gap_re = re.compile(
            r'([+-])\s+(\d)')
    _item_name_re = re.compile(
            r'<span class="r(\d+) item-name">([^<]+)</span>')

    _rarity_colors = {
            u'6': u'orange',
            u'5': u'bright magenta',
            u'4': u'bright blue',
            u'3': u'bright green',
            u'2': u'white',
            u'1': u'light gray'}

    def __init__(self, madcow=None):
        self.madcow = madcow
        if madcow:
            self.colorlib = madcow.colorlib
        else:
            self.colorlib = ColorLib(u'ansi')

    def lookup_item(self, item):
        page = geturl(self._search_url, opts={u'search_text': item})
        item = item.lower()
        redirect = self._redirect_re.search(page)
        if redirect:
            url = urljoin(self._base_url, redirect.group(1))
            page = geturl(url)
        elif u'Search results for' in page:
            items = self._results_re.findall(page)
            if not items:
                return
            items = [(v.lower(), k) for k, v in items]
            items = sorted(items)
            map = dict(items)
            if item in map:
                url = map[item]
            else:
                url = items[0][1]
            page = geturl(url)
        bonus = u', '.join(self._bonus_re.findall(page))
        bonus = self._stat_gap_re.sub(r'\1\2', bonus)
        if not bonus:
            bonus = u'No bonuses'
        rarity, name = self._item_name_re.search(page).groups()
        color = self._rarity_colors[rarity]
        name = name.replace('\\', '')
        name = name.strip()
        name = self.colorlib.get_color(color, text=name)
        return u'%s: %s' % (name, bonus)

    def response(self, nick, args, kwargs):

        def output(response):
            if self.madcow:
                self.madcow.output(response, kwargs['req'])
            else:
                print response

        try:
            for item in self._items_re.findall(args[0]):
                response = self.lookup_item(item)
                if response:
                    output(response)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
