"""Cut past bo.lt stuff"""

from django.conf import settings
from gruntle.memebot.scanner import Scanner, ScanResult, image
from gruntle.memebot.exceptions import InvalidContent, trapped
from gruntle.memebot.utils.browser import render_node

class BoltScanner(Scanner):

    rss_template = None

    url_match = {'netloc_regex': r'^reddit.bo.lt$',
                 'netloc_ignorecase': True,
                 }

    def handle(self, response, log, browser):
        with trapped:
            url = response.data.body.find('img', style="max-width: 100%")['src']
            return image.scanner.handle(browser.open(url), log, browser)
        raise InvalidContent(response, 'could not parse image from bolt page')


scanner = BoltScanner()
