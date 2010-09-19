"""Module stub"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import getsoup
from urlparse import urljoin

class Main(Module):

    pattern = re.compile(r'^\s*urban(?:\s+(.+?)(?:\s+(\d+))?)?\s*$', re.I)
    help = 'urban <term> [#] - lookup word/phrase on urban dictionary'
    error = u'So obscure, not even urban dictionary knows it'

    urban_url = 'http://www.urbandictionary.com/'
    urban_search = urljoin(urban_url, '/define.php')
    urban_random = urljoin(urban_url, '/random.php')

    entry_re = re.compile(r'entry_\d+')
    newline_re = re.compile(r'(?:\r\n|[\r\n])')

    RESULTS_PER_PAGE = 7

    def response(self, nick, args, kwargs):
        query, idx = args
        if query:
            if idx:
                idx = int(idx)
            response = self.lookup(query, idx)
        else:
            response = self.random()
        return u'%s: %s' % (nick, response)

    def lookup(self, query, idx=None):
        """Look up term on urban dictionary"""
        if idx is None:
            idx = 1
        orig_idx = idx
        page = int(idx / self.RESULTS_PER_PAGE)
        idx = (idx % self.RESULTS_PER_PAGE) - 1
        if idx == -1:
            idx = 6
        soup = getsoup(self.urban_search, {'term': query, 'page': page},
                       referer=self.urban_url)
        return self.parse(soup, idx, page, orig_idx)

    def random(self):
        """Get a random definition"""
        soup = getsoup(self.urban_random, referer=self.urban_url)
        return self.parse(soup)

    def parse(self, soup, idx=1, current_page=1, orig_idx=1):
        """Parse page for definition"""

        # get definition
        table = soup.body.find('table', id='entries')
        word = self.render(table.find('td', 'word'))
        entries = table('td', 'text', id=self.entry_re)
        size = len(entries)
        if not size:
            raise ValueError('no results?')
        if idx >= size:
            idx = size - 1
        entry = entries[idx]

        # torturous logic to guess number of entries
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
                total = ((highest - 1) * self.RESULTS_PER_PAGE) + len(entries)
            else:
                total = highest * self.RESULTS_PER_PAGE
        if orig_idx > total:
            orig_idx = total

        # construct page
        result = u'[%d/%d] %s: ' % (orig_idx, total, word)
        result += self.render(entry.find('div', 'definition'))
        try:
            example = self.render(entry.find('div', 'example'))
            result += u' - Example: %s' % example
        except:
            pass
        return result

    @staticmethod
    def render(node):
        """Render node to text"""
        data = node.renderContents()
        if isinstance(data, str):
            data = data.decode('utf-8', 'ignore')
        return Main.newline_re.sub(' ', strip_html(data)).strip()
