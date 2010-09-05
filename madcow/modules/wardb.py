"""Lookup Warhammer Online items"""

from madcow.util import Module
import re
from madcow.util.http import geturl
from urlparse import urljoin
from madcow.util.color import ColorLib

class Main(Module):

    pattern = re.compile(r'^\s*wardb\s+(.+?)\s*$', re.I)
    require_addressing = True
    help = u'wardb <item> - look up warhammer item stats'

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

    def init(self):
        self.colorlib = self.madcow.colorlib

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
        return self.lookup_item(args[0])
