"""look up offensive definitions in urban dictionary"""

from urlparse import urljoin
import re

from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from madcow.util.text import decode


RESULTS_PER_PAGE = 7

_urban_url = 'http://www.urbandictionary.com/'
_urban_search = urljoin(_urban_url, '/define.php')
_urban_random = urljoin(_urban_url, '/random.php')


class Main(Module):

    pattern = re.compile(r'^\s*urban(?:\s+(.+?)(?:\s+(\d+))?)?\s*$', re.I)
    help = 'urban <term> [#] - lookup word/phrase on urban dictionary'
    error = u'So obscure, not even urban dictionary knows it'

    def response(self, nick, args, kwargs):
        query, idx = args
        try:
            if query:
                if idx:
                    idx = int(idx)
                res = self.lookup(query, idx)
            else:
                res = self.parse(getsoup(_urban_random, referer=_urban_url))
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            res = u"That doesn't even exist in urban dictionary, stop making stuff up."
        return u'{}: {}'.format(nick, res)

    def lookup(self, query, idx=None):
        """Look up term on urban dictionary"""
        if idx is None:
            idx = 1
        orig_idx = idx
        page = int(idx / RESULTS_PER_PAGE)
        idx = (idx % RESULTS_PER_PAGE) - 1
        if idx == -1:
            idx = 6
        return self.parse(getsoup(_urban_search,
                                  {'term': query, 'page': page},
                                  referer=_urban_url,),
                          idx, page, orig_idx)

    def parse(self, soup, idx=1, current_page=1, orig_idx=1):
        """Parse page for definition"""
        table = soup.body.find('div', id='content')
        entries = table('div', 'box')
        size = len(entries)
        if not size:
            raise ValueError('no results?')
        if idx >= size:
            idx = size - 1
        entry = entries[idx]

        # torturous logic to guess number of entries by multiplying page count
        # with observed items per page. note that since both of these values
        # are apparently estimates with little basis in reality, the result is
        # complete fiction. this misfeature is actually more trouble than it
        # is worth since all it accomplishes is confusing people, while never
        # managing to guess correctly. that is why i am leaving it in.
        pages = soup.body.find('div', 'pagination')
        if pages is None:
            total = len(entries)
        else:
            highest = 0
            for a in pages('a'):
                try:
                    page = int(a['href'].split('page=')[1])
                except IndexError:
                    continue
                if page > highest:
                    highest = page
            if highest == current_page:
                total = ((highest - 1) * RESULTS_PER_PAGE) + len(entries)
            else:
                total = highest * RESULTS_PER_PAGE
        if orig_idx > total:
            orig_idx = total
        result = u'[{}/{}] {}: {}'.format(orig_idx, total,
                                          render(table.find('div', 'word')),
                                          render(entry.find('div', 'meaning')))
        try:
            result += u' - Example: ' + self.render(entry.find('div', 'example'))
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            pass
        return result


def render(node, _newline_re=re.compile(r'(?:\r\n|[\r\n])')):
    """Render node to text"""
    data = node.renderContents()
    if isinstance(data, str):
        data = decode(data, 'utf-8')
    return _newline_re.sub(' ', strip_html(data)).strip()

