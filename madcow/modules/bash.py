#!/usr/bin/env python

"""Interface for getting really stupid IRC quotes"""

import re
import random
from madcow.util import Module, strip_html
from madcow.util.http import geturl

class Bash(object):

    random = u'http://www.bash.org/?random'
    bynum = u'http://www.bash.org/?num'
    search = u'http://www.bash.org/'
    query = 'search'
    opts = dict(show=100)
    entries = re.compile(u'<p class="qt">(.*?)</p>', re.DOTALL)


class QDB(object):

    random = 'http://qdb.us/random'
    bynum = 'http://qdb.us/num'
    search = 'http://qdb.us/'
    query = 'search'
    opts = dict(limit=100, approved=1)
    entries = re.compile(r'<span class=qt[^>]*>(.*?)</span>', re.DOTALL)


class Limerick(object):

    random = u'http://www.limerickdb.com/?random'
    bynum = u'http://www.limerickdb.com/?num'
    search = u'http://www.limerickdb.com/'
    query = 'search'
    opts = dict(number=100)
    entries = re.compile(u'<div class="quote_output">\s*(.*?)\s*</div>',
                         re.DOTALL)


class Main(Module):

    pattern = re.compile(u'^\s*(bash|qdb|limerick)(?:\s+(\S+))?', re.I)
    require_addressing = True
    help = u'<bash|qdb|limerick> [#|query] - get stupid IRC quotes'
    sources = {u'bash': Bash(), u'qdb': QDB(), u'limerick': Limerick()}
    error = u'Having some issues, make some stupid quotes yourself'

    def response(self, nick, args, kwargs):
        source = self.sources[args[0]]
        try:
            query = args[1]
        except:
            query = None
        try:
            num = int(query)
            query = None
        except:
            num = None
        if num:
            url = source.bynum.replace(u'num', unicode(num))
            opts = None
        elif query:
            url = source.search
            opts = dict(source.opts)
            opts[source.query] = query
        else:
            url = source.random
            opts = None
        doc = geturl(url, opts=opts)
        entries = source.entries.findall(doc)
        if query:
            entries = filter(None, entries)
        entry = random.choice(entries)
        return '\n'.join(filter(None, strip_html(entry).strip().splitlines()))
