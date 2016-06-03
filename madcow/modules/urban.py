"""look up offensive definitions in urban dictionary"""

from urlparse import urljoin
import re

from madcow.util import Module, strip_html
from madcow.util.http import getsoup, geturlopt
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
        kwargs['req'].quoted = True
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
            self.log.exception('error parsing query: {}'.format(query))
            res = u"That doesn't even exist in urban dictionary, stop making stuff up."
        return u'{}: {}'.format(nick, res)

    def lookup(self, query, idx=None):
        """Look up term on urban dictionary"""
        if idx is None:
            idx = 1
        orig_idx = idx
        page, idx = divmod(idx, RESULTS_PER_PAGE)
        if idx:
            page += 1
        return self.parse(getsoup(_urban_search,
            referer=_urban_url, term=query, page=page),
            idx - 1, page, orig_idx)

    def parse(self, soup, idx=1, current_page=1, orig_idx=1):
        """Parse page for definition"""
        entries = soup.body('div', 'meaning')
        size = len(entries)
        if not size:
            raise ValueError('no results?')
        if idx >= size:
            idx = size - 1
        entry = entries[idx]
        pages = soup.body.find('ul', 'pagination')
        if pages is None:
            total = len(entries)
        else:
            last = pages.find('a', text=re.compile('Last'))
            highest = current_page
            if last is not None:
                last = geturlopt(last.parent['href'], 'page')
                if last:
                    highest = int(last)
            if highest == current_page:
                total = ((highest - 1) * RESULTS_PER_PAGE) + len(entries)
            else:
                total = highest * RESULTS_PER_PAGE
        if orig_idx > total:
            orig_idx = total
        result = u'[{}/{}] {}: {}'.format(
                orig_idx,
                total,
                render(entry.findPreviousSibling('div', 'def-header').find('a', 'word')),
                render(entry),
                )
        try:
            result += u' - Example: ' + render(entry.findNextSibling('div', 'example'))
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

