"""Extract image from gallery view of imgur links, but grab the title on the way"""

from gruntle.memebot.utils.browser import decode_entities
from gruntle.memebot.scanner.image import ImageScanner
from gruntle.memebot.exceptions import trapped
from gruntle.memebot.scanner import ScanResult
from gruntle.memebot.utils import text

class IMGurScanner(ImageScanner):

    url_match = {'netloc_regex': r'^(?:www\.)?imgur\.com$', 'netloc_ignorecase': True}

    def handle(self, response, log, browser):
        if response.data_type != 'soup':
            raise InvalidContent(response, 'Not an HTML file')
        soup = response.data

        title = None
        with trapped:
            title = decode_entities(text.decode(soup.head.title.string).strip()) .replace(' - Imgur', '')

        with trapped:
            url = soup.head.find('link', rel='image_src')['href']
            response = browser.open(url)  # move max_read/etc. to __init__ so it doesn't get bypassed like this
            result = super(IMGurScanner, self).handle(response, log, browser)
            return ScanResult(response=result.response,
                              override_url=result.override_url,
                              title=result.title if title is None else title,
                              content_type=result.content_type,
                              content=result.content,
                              attr=result.attr)

        raise InvalidContent(response, "Couldn't find the image")


scanner = IMGurScanner()
