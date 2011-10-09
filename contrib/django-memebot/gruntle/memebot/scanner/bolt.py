"""Extract image from gallery view of imgur links, but grab the title on the way"""

from gruntle.memebot.scanner.image import ImageScanner
from gruntle.memebot.exceptions import trapped

class BoltScanner(ImageScanner):

    url_match = {'netloc_regex': r'^reddit.bo.lt$', 'netloc_ignorecase': True}

    def handle(self, response, log, browser):
        with trapped:
            url = response.data.body.find('img', style="max-width: 100%")['src']
            response = browser.open(url, follow_meta_redirect=True)
            return super(BoltScanner, self).handle(response, log, browser)
        raise InvalidContent(response, 'could not parse image from bolt page')


scanner = BoltScanner()
