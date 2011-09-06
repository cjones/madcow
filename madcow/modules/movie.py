"""Rate movies on IMDB/RT/MetaCritic"""

from madcow.util.http import geturl, getsoup
from urlparse import urljoin
import re
from BeautifulSoup import BeautifulSoup
from madcow.util import Module, strip_html

class Main(Module):

    """Module object loaded by madcow"""

    # module attributes
    pattern = re.compile(r'^\s*(?:(rate)\s+(.+?)|(topmovies))\s*$', re.I)
    help = 'rate <movie> - get rating for named movie'
    help += '\ntopmovies - list top 10 box office movies'

    # urls
    rt_url = 'http://www.rottentomatoes.com/'
    rt_search = urljoin(rt_url, '/search/full_search.php')
    imdb_url = 'http://www.imdb.com/'
    imdb_search = urljoin(imdb_url, '/find')
    imdb_top = urljoin(imdb_url, '/chart/')

    # normalization regex
    year_re = re.compile(r'\(\d{4}\)\s*$')
    rev_article_re = re.compile(r'^(.*?),\s*(the|an?)\s*$', re.I)
    articles_re = re.compile(r'^\s*(the|an?)\s+', re.I)
    badchars_re = re.compile(r'[^a-z0-9 ]', re.I)
    whitespace_re = re.compile(r'\s+')
    and_re = re.compile(r'\s+and\s+', re.I)

    def init(self):
        self.sources = [('IMDB', self.rate_imdb), ('RT', self.rate_rt)]

    def response(self, nick, args, kwargs):
        if args[0] == 'rate':
            response = self.rate(args[1])
        elif args[2] == 'topmovies':
            response = self.gettop()
        else:
            raise ValueError('invalid args')
        return u'%s: %s' % (nick, response)

    def rate(self, name):
        """Get rating for name"""
        normalized = self.normalize(name)
        out = []
        for source, func in self.sources:
            try:
                title, rating = func(name)
                if self.normalize(title) != normalized:
                    rating = '[%s] %s' % (title, rating)
                rating = rating.strip()
                out.append('%s: %s' % (source, rating))
            except:
                self.log.exception('no match')
                pass
        if not out:
            out.append('No match')
        return ', '.join(out)

    def rate_rt(self, name):
        """Rating from rotten tomatoes"""
        soup = getsoup(self.rt_search, {'search': name}, referer=self.rt_url)
        ourname = self.normalize(name)
        results = soup.find('ul', id='movie_results_ul')
        if results is None:
            rating = soup.find('span', id='all-critics-meter').renderContents() + '%'
            title = strip_html(soup.find('h1', 'movie_title').renderContents().encode('utf-8', 'ignore')).strip()
            return title, rating
        else:
            for result in results('li'):
                try:
                    rating = strip_html(result.find('span', 'tMeterScore').renderContents()).strip()
                    title = strip_html(result.find('div', 'media_block_content').h3.a.renderContents()).strip()
                    if ourname == self.normalize(title):
                        return title, rating
                except AttributeError:
                    pass

    def rate_imdb(self, name):
        """Get user rating from IMDB"""
        page = geturl(self.imdb_search, {'s': 'tt', 'q': name}, referer=self.imdb_url)
        soup = BeautifulSoup(page)
        if soup.title.renderContents() == 'IMDb Title Search':
            main = soup.body.find('div', id='main')
            name = self.normalize(name)
            url = None
            for p in main('p'):
                if p.b is not None:
                    section = p.b.renderContents()
                    if section in ('Titles (Exact Matches)', 'Popular Titles', 'Titles (Partial Matches)'):
                        for a in p('a'):
                            text = a.renderContents()
                            if text:
                                normalized = self.normalize(text)
                                if normalized == name:
                                    url = urljoin(self.imdb_url, a['href'])
                                    break
                        if url:
                            break
            else:
                raise ValueError('no exact matches')
            soup = BeautifulSoup(geturl(url, referer=self.imdb_search))
        rating = soup.find('span', itemprop='ratingValue').renderContents()
        realname = strip_html(soup.title.renderContents().replace(' - IMDb', ''))
        return realname, rating

    def gettop(self):
        """Get box office ratings"""
        soup = BeautifulSoup(geturl(self.imdb_top))
        table = soup.body.find('div', id='boxoffice').table
        data = []
        for row in table('tr')[1:]:
            items = row('td')
            data.append({'title': strip_html(items[2].a.renderContents()),
                         'weekend': items[3].renderContents().strip(),
                         'gross': items[4].renderContents().strip()})
        tsize = max(len(item['title']) for item in data)
        wsize = max(len(item['weekend']) for item in data)
        gsize = max(len(item['gross']) for item in data)
        output = ['# / Title / Weekend / Gross']
        for i, item in enumerate(data):
            output.append('%s %s - %s / %s' % (
                    str(i + 1).rjust(2),
                    item['title'].ljust(tsize),
                    item['weekend'].ljust(wsize),
                    item['gross'].ljust(gsize)))
        return '\n'.join(output)

    def normalize(self, name):
        """Normalize a movie title for easy comparison"""
        name = strip_html(name)
        name = self.year_re.sub('', name)              # strip trailing year
        name = self.rev_article_re.sub(r'\2 \1', name) # Movie, The = The Movie
        name = self.articles_re.sub('', name)          # strip leading the/an
        name = self.badchars_re.sub(' ', name)         # only allow alnum
        name = name.lower()                            # lowercase only
        name = name.strip()                            # strip whitespace
        name = self.whitespace_re.sub(' ', name)       # compress whitespace
        name = self.and_re.sub(' ', name)              # the word "and"
        return name
