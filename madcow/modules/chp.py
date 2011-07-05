#!/usr/bin/env python

"""Get traffic info from CHP website (bay area only)"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup

class Main(Module):

    pattern = re.compile(u'^\s*chp\s+(.+)', re.I)
    require_addressing = True
    help = u'chp <highway> - look for CHP reports for highway, such as 101'
    url = u'http://cad.chp.ca.gov/Traffic.aspx'
    incidents = re.compile(u'<tr>(.*?)</tr>', re.DOTALL)
    data = re.compile(u'<td class="T".*?>(.*?)</td>')
    clean = re.compile(u'[^0-9a-z ]', re.I)
    error = u'I failed to perform that lookup'

    def response(self, nick, args, kwargs):
        query = args[0]
        check = self.clean.sub(u'', query)
        check = re.compile(re.escape(check), re.I)

        results = []
        page = getsoup(self.url)
        table = page.find('table', id='gvIncidents')
        rows = table('tr')[1:]
        for row in rows:
            _, num, time, type, loc, coord, area = [
                    strip_html(cell.renderContents())
                    for cell in row('td')
                    ]
            if check.search(loc):
                results.append(u'=> %s: %s (%s) %s' % (time, loc, area, type))
        if len(results) > 0:
            return u'\n'.join(results)
        else:
            return u'%s: No incidents found' % nick
