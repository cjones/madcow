"""Looks for image links to cache locally"""

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

try:
    from PIL import Image
except ImportError:
    Image = None

from django.conf import settings
from gruntle.memebot.scanner import Scanner, ScanResult, InvalidContent, ConfigError

class ImageScanner(Scanner):

    rss_template = 'memebot/scanner/rss/image.html'

    def __init__(self, *args, **kwargs):
        image_max_size = kwargs.pop('image_max_size', None)
        image_resize_alg = kwargs.pop('image_resize_alg', None)
        image_type = kwargs.pop('image_type', None)

        super(ImageScanner, self).__init__(*args, **kwargs)

        if image_max_size is None:
            image_max_size = settings.SCANNER_IMAGE_MAX_SIZE
        if image_resize_alg is None:
            image_resize_alg = settings.SCANNER_IMAGE_RESIZE_ALG
        if image_type is None:
            image_type = settings.SCANNER_IMAGE_TYPE

        if isinstance(image_resize_alg, (str, unicode)):
            image_resize_alg = getattr(Image, image_resize_alg, None)
        if image_resize_alg is None:
            raise ConfigError('image resize algorithm invalid')

        self.image_max_size = image_max_size
        self.image_resize_alg = image_resize_alg
        self.image_type = image_type.lower()

    @property
    def image_format(self):
        return self.image_type.upper()

    @property
    def content_type(self):
        return 'image/' + self.image_type

    def handle(self, response, log):
        if Image is None:
            raise InvalidContent(response, 'PIL is not installed, cannot process')
        if response.data_type != 'image':
            raise InvalidContent(response, 'Not an image')

        image = response.data
        log.info('Detected %s image (%d x %d)', image.format, *image.size)

        # resize images before caching
        ratios = set(float(msize) / size for size, msize in zip(image.size, self.image_max_size) if size > msize)
        if ratios:
            ratio = min(ratios)
            new_size = tuple(int(size * ratio) for size in image.size)
            log.info('Rescaling to: %d x %d', *new_size)
            image = image.resize(new_size, self.image_resize_alg)

        # save as specified file via string buffer
        fileobj = stringio.StringIO()
        image.save(fileobj, self.image_format)

        return ScanResult(response=response,
                          override_url=None,
                          title=None,
                          content_type=self.content_type,
                          content=fileobj.getvalue())


scanner = ImageScanner()
