#!/usr/bin/env python

"""Module stub"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from urlparse import urljoin

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008'
__all__ = []

class Main(Module):
    pattern = re.compile(r'^\s*traffic\s+from\s+(.+?)\s+to\s+(.+?)\s*$', re.I)
    help = 'traffic from <loc> to <loc> - get report'
    error = "couldn't look that up"
    base_url = 'http://traffic.511.org/'
    start_url = urljoin(base_url, '/traffic_text.asp')
    second_url = urljoin(base_url, '/traffic_text2.asp')
    report_url = urljoin(base_url, '/traffic_text3.asp')
    re_loc = re.compile(r"([cmx])\('([^']+)'\);")
    re_origin = re.compile(r'<input name="origin" type="hidden" value="(\d+)">')
    re_trip = re.compile(r'<p><b>Trip \S:\s+([0-9.]+)\s+min\.</b>\s+.*?\(([0-9.]+)\s+miles\).*?(<table.*?</table>)', re.I+re.DOTALL)
    re_rows = re.compile(r'<tr.*?</tr>', re.I+re.DOTALL)
    re_cells = re.compile(r'<td.*?</td>', re.I+re.DOTALL)
    re_tags = re.compile(r'<.*?>', re.DOTALL)

    def __init__(self, madcow=None):
        self.locs = {}

    def get_locations(self, reload=False):
        if not self.locs or reload:
            page = geturl(self.start_url)
            self.locs = {}
            c = m = None
            for loc_type, loc in self.re_loc.findall(page):
                if loc_type == 'c':
                    c = loc
                    self.locs.setdefault(c, {})
                elif loc_type == 'm':
                    m = loc
                    self.locs[c].setdefault(m, [])
                elif loc_type == 'x':
                    self.locs[c][m].append(loc)
        return self.locs

    def get_location_data(self, loc):
        locs = self.get_locations()
        for c, mx in locs.items():
            if loc.lower() == c.lower():
                m, x = mx.items()[0]
                x = x[0]
                break
        return c, m, x

    def response(self, nick, args, kwargs):
        try:
            from_loc = self.get_location_data(args[0])
            to_loc = self.get_location_data(args[1])
            opts = {
                'city': from_loc[0],
                'main': from_loc[1],
                'cross': from_loc[2],
            }
            page = geturl(self.second_url, opts=opts, referer=self.start_url)
            origin = self.re_origin.search(page).group(1)
            opts = {
                'city': to_loc[0],
                'main': to_loc[1],
                'cross': to_loc[2],
                'origin': origin,
                'originCity': from_loc[0],
                'originMain': from_loc[1],
                'originCross': from_loc[2],
            }
            page = geturl(self.report_url, opts=opts, referer=self.second_url)
            time, miles, table = self.re_trip.search(page).groups()
            rows = self.re_rows.findall(table)[2:]
            speeds = []
            for row in rows:
                try:
                    road, speed = self.re_cells.findall(row)[:2]
                    road = self.re_tags.sub('', road)
                    road = road.replace(' ', '')
                    speed = self.re_tags.sub('', speed)
                    speed = speed.replace(' or higher', '')
                    speeds.append('%s=%s' % (road, speed))
                except:
                    continue
            speeds = ', '.join(speeds)
            return '%s: %s mins. (%s miles) [%s]' % (nick, time, miles, speeds)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
