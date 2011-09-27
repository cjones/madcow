"""Extracts summary data from HTML pages if possible"""

from gruntle.memebot.scanner import Scanner, InvalidContent, ScanResult
from gruntle.memebot.utils import trapped, text

class HTMLScanner(Scanner):

    rss_template = 'memebot/scanner/rss/html.html'

    def handle(self, response, log):
        if response.data_type != 'soup':
            raise InvalidContent(response, 'Not an HTML file')
        soup = response.data

        title = None
        with trapped:
            title = text.decode(soup.head.title.string).strip()
            log.info('Title: %r', title)


        # XXX remove me when we make some progress :(
        raise InvalidContent('not ready to use this yet')
        return ScanResult(response=response,
                          override_url=None,
                          title=title,
                          content_type=None,
                          content=None)


scanner = HTMLScanner()
