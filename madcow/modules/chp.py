#!/usr/bin/env python

"""Get traffic info from CHP website (bay area only)"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import geturl

class Main(Module):

    pattern = re.compile(u'^\s*chp\s+(.+)', re.I)
    require_addressing = True
    help = u'chp <highway> - look for CHP reports for highway, such as 101'
    url = u'http://cad.chp.ca.gov/sa_list.asp?centerin=GGCC&style=l'
    incidents = re.compile(u'<tr>(.*?)</tr>', re.DOTALL)
    data = re.compile(u'<td class="T".*?>(.*?)</td>')
    clean = re.compile(u'[^0-9a-z ]', re.I)
    error = u'I failed to perform that lookup'

    def response(self, nick, args, kwargs):
        query = args[0]
        check = self.clean.sub(u'', query)
        check = re.compile(check, re.I)
        results = []
        doc = geturl(self.url)
        for i in self.incidents.findall(doc):
            data = [strip_html(c) for c in self.data.findall(i)][1:]
            if len(data) != 4:
                continue
            if check.search(data[2]):
                results.append(u'=> %s: %s - %s - %s' % (data[0], data[1],
                                                         data[2], data[3]))

        if len(results) > 0:
            return u'\n'.join(results)
        else:
            return u'%s: No incidents found' % nick
