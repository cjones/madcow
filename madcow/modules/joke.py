"""Get a random joke"""

from madcow.util import Module, strip_html
from madcow.util.http import geturl
import re
from urlparse import urljoin
import urllib

class Main(Module):

    pattern = re.compile(r'^\s*joke(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True
    help = (u'joke <oneliners | news | signs | nerd | professional | quotes | '
            u'lightbulb | couples | riddles | religion | gross | blonde | poli'
            u'tics | doit | laws | defs | dirty | ethnic | zippergate> - displ'
            u'ays a random joke')
    baseurl = u'http://www.randomjoke.com/topic/'
    random_url = urljoin(baseurl, u'haha.php')
    joke = re.compile(r'next.joke.*?<P>(.*?)<CENTER>', re.DOTALL)

    def response(self, nick, args, kwargs):
        query = args[0]
        if query is None or query == u'':
            url = self.random_url
        else:
            query = u' '.join(query.split())
            query = query.replace(u' ', u'_')
            query = query.encode('utf-8', 'replace')
            query = urllib.quote(query) + u'.php'
            url = urljoin(self.baseurl, query)
        doc = geturl(url)
        result = self.joke.findall(doc)[0]
        result = strip_html(result)

        # cleanup output a bit.. some funny whitespace in it -cj
        result = result.replace(u'\x14', u' ')
        result = result.replace(u'\n', u' ')
        result = re.sub(r'\s{2,}', u' ', result)
        return result.strip()
