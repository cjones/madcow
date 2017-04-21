"""Extract image from gallery view of imgur links, but grab the title on the way"""

from memebot.utils.browser import render_node, strip_site_name
from memebot.utils.browser import decode_entities
from memebot.scanner.image import ImageScanner
from memebot.exceptions import InvalidContent, trapped
from memebot.scanner import ScanResult

class IMGurScanner(ImageScanner):

    url_match = {'netloc_regex': r'^(?:www\.)?imgur\.com$', 'netloc_ignorecase': True}

    def handle(self, response, log, browser):
        if response.data_type != 'soup':
            raise InvalidContent(response, 'Not an HTML file')
        soup = response.data

        title = None
        with trapped:
            title = strip_site_name(render_node(soup.head.title), response.url)

        with trapped:
            url = soup.head.find('link', rel='image_src')['href']
            response = browser.open(url, follow_meta_redirect=True)
            result = super(IMGurScanner, self).handle(response, log, browser)
            return ScanResult(response=result.response,
                              override_url=result.override_url,
                              title=result.title if title is None else title,
                              content_type=result.content_type,
                              content=result.content,
                              attr=result.attr)

        raise InvalidContent(response, "Couldn't find the image")


scanner = IMGurScanner()
