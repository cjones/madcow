"""Extracts summary data from HTML pages if possible"""

import re
from BeautifulSoup import BeautifulSoup, NavigableString
from gruntle.memebot.scanner import Scanner, ScanResult
from gruntle.memebot.exceptions import InvalidContent, trapped
from gruntle.memebot.utils import text, browser
from gruntle.memebot.utils.browser import render_node, strip_site_name
from django.conf import settings

tag_re = re.compile(r'(</?(\w+)[^>]*>)')

class HTMLScanner(Scanner):

    rss_templates = {None: 'memebot/scanner/rss/html.html'}

    def __init__(self, *args, **kwargs):
        summary_size = kwargs.pop('summary_size', None)
        summary_cont = kwargs.pop('summary_cont', None)
        super(HTMLScanner, self).__init__(*args, **kwargs)
        if summary_size is None:
            summary_size = settings.FEED_SUMMARY_SIZE
        if summary_cont is None:
            summary_cont = settings.FEED_SUMMARY_CONT
        self.summary_size = summary_size
        self.summary_cont = summary_cont

    def handle(self, response, log, browser):
        if response.data_type != 'soup':
            raise InvalidContent(response, 'Not an HTML file')
        soup = response.data
        title = summary = content_type = None

        with trapped:
            title = strip_site_name(render_node(soup.head.title), response.url)

        with trapped:
            summary = self.summarize_soup(soup)
            content_type = 'text/plain'

        if title is None and summary is None and content_type is None:
            raise InvalidContent("couldn't get anything useful out of that..")

        return ScanResult(response=response,
                          override_url=None,
                          title=title,
                          content_type=content_type,
                          content=summary,
                          attr=None)

    def summarize_soup(self, soup):
        """
        Experimental: Try to guess where the main content is and return summary text.
        In it's current form, picking news sites & articles at random, it seems to have
        just slightly better than a 50% chance of working right. The other time it finds
        total garbage. Better than nothing for a first attempt, I guess ...
        """

        # first, lean up the html a little bit and then remove every tag
        # that isn't a <div> or <p> tag. theory being that the latter two are mostly
        # the ones that define the structure of the document, which is what we
        # are most interested in. well, its structure relative to whatever text nodes
        # are left over.
        html = text.decode(browser.prettify_node(soup.body))
        for orig, name in tag_re.findall(html):
            if name not in ('div', 'p'):
                html = html.replace(orig, u' ')

        # put it back into soup form and perform the main logic thingy here. the idea
        # is to walk each remaining node in the branch and look at the text contents of
        # each of its *siblings*. the idea is that these would be paragraphs in the article.
        # this falls apart spectacularly on some sites, and in a very specific way. I thin
        # certain menus or sidebars are laid out this way too. since we do a basic word count, if
        # they are large enough, they'll overtake the article. perhaps we can correct for this
        # in another way.. requires investigation.
        soup = BeautifulSoup(html)
        blocks = []
        for node in soup.findAll(True):
            size = 0
            for p in node:
                for el in p:
                    if isinstance(el, NavigableString):
                        size += len(el)
            if size:
                blocks.append((size, node))

        # now we have a list of nodes & how much text in "paragraph" form they contain. whatever is
        # the largest we will assume is the intended content, and grab a cleaned up snippet from
        # the front of it.
        if blocks:
            article = browser.render_node(max(blocks)[1])
            words = article[:self.summary_size].split()
            if len(article) > self.summary_size:
                words[-1] = self.summary_cont
            return u' '.join(words)


scanner = HTMLScanner()
