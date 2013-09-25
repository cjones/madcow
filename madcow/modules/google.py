"""I'm feeling lucky"""

from madcow.util import Module, strip_html
from madcow.util.text import decode
from madcow.util.http import getsoup, urllib
import re
from madcow.util.google import Google


class Main(Module):

    pattern = re.compile(r'^(?:search|g(?:oog(?:le)?)?)\s+(.+)\s*$', re.I)
    require_addressing = True
    help = u"(g[oog[le]]|search) <query> - Will return 3 first results"
    error = u'not so lucky today..'

    def init(self):
        self.google = Google()

    def response(self, nick, args, kwargs):
        query = args[0]
        sopa = getsoup(self.google.find(query))
        contador = 1  # Yay for the mexican dev
        myretval = u''
        for li in sopa.body('div', {'id': 'ires'})[0].ol('li'):
            if contador > 3:
                break

            name = strip_html(decode(li.h3.renderContents()))
            urlpluscrap = li.h3.a['href'].replace('/url?q=', '')
            url = urllib.unquote(urlpluscrap.split('&sa')[0])
            myretval += u'{}: {} \n'.format(name, url)
            contador += 1

        return myretval
