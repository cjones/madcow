#!/usr/bin/env python

if __name__ == '__main__':
    import os
    args = ['./manage.py', 'scanner', '-n']
    os.chdir('/home/cjones/proj')
    os.execvp(args[0], args)
    os._exit(1)

"""Core handler for scanning Link objects"""

import datetime

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

from django.conf import settings

try:
    from PIL import Image
except ImportError:
    Image = None

from gruntle.memebot.utils import TrapError, TrapErrors, locking, text, plural, get_logger
from gruntle.memebot.utils.browser import Browser
from gruntle.memebot.decorators import logged
from gruntle.memebot.models import Link

@logged('scanner', append=True)
def run(log, user_agent=None,
                       max_links=None,
                       max_read=None,
                       max_errors=None,
                       dry_run=False,
                       image_type=None,
                       image_max_size=None,
                       image_resize_alg=None,
                       ):

    """Run pending links through scanner"""

    with locking.Lock('scanner', 0):

        # get links to process
        if max_links is None:
            max_links = settings.SCANNER_MAX_LINKS
        links = Link.objects.filter(state='new').order_by('created')
        if max_links is not None:
            links = links[:max_links]
        num_links = links.count()

        if num_links:

            # defaults from settings
            if user_agent is None:
                user_agent = settings.SCANNER_USER_AGENT
            if max_read is None:
                max_read = settings.SCANNER_MAX_READ
            if max_errors is None:
                max_errors = settings.SCANNER_MAX_ERRORS
            if image_type is None:
                image_type = settings.SCANNER_IMAGE_TYPE
            if image_max_size is None:
                image_max_size = settings.SCANNER_IMAGE_MAX_SIZE
            if image_resize_alg is None:
                image_resize_alg = settings.SCANNER_IMAGE_RESIZE_ALG
                if isinstance(image_resize_alg, (str, unicode)):
                    image_resize_alg = getattr(Image, image_resize_alg)

            browser = Browser(user_agent=user_agent)
            for i, link in enumerate(links):
                log = log.get_named_child('%d/%d' % (i + 1, num_links))
                log.info('Scanning: %s', link.url)
                fatal = False
                try:
                    with TrapErrors():
                        response = browser.open(link.url, max_read=max_read)
                        if response.is_valid:
                            log.info('URL is valid')
                            publish = True
                            link.resolved_url = response.real_url

                            if link.url != response.real_url:
                                log.info('Redirected: %s', response.real_url)

                            # a hotlinked image
                            if response.data_type == 'image' and Image is not None:
                                image = response.data
                                log.info('Content: %s image, size = %d x %d', image.format, *image.size)

                                # resize if too large
                                ratios = set(float(msize) / size
                                             for size, msize in zip(image.size, image_max_size)
                                             if size > msize)

                                if ratios:
                                    ratio = min(ratios)
                                    new_size = tuple(int(size * ratio) for size in image.size)
                                    log.info('Rescaling to: %d x %d', *new_size)
                                    image = image.resize(new_size, image_resize_alg)

                                # save as specified format
                                link.mime_type = 'image/%s' % image_type.lower()
                                link.content_type = 'image'
                                fileobj = stringio.StringIO()
                                image.save(fileobj, image_type.upper())
                                link.content = fileobj.getvalue()

                            # html page.. extract some info
                            elif response.data_type == 'soup':
                                log.info('Content: HTML page')

                                # get title of page
                                with trapped:
                                    link.title = text.decode(response.data.title.string).strip()
                                    log.info('Title: %r', link.title)

                            # no idea.. just save what we got
                            else:
                                log.info('Content: Unknown (%s)', response.mime_type)
                                link.mime_type = response.mime_type

                        else:
                            log.info('Error: %d %s', response.code, response.msg)
                            publish = False
                            link.content_type = 'error'
                            link.content = response.msg
                            if response.code == 404:
                                fatal = True

                except TrapError, exc:
                    log.warn('Failure scanning link', exc_info=exc.args)
                    link.content_type = 'error'
                    link.content = exc
                    publish = False

                if publish:
                    link.publish(commit=False)
                else:
                    link.error_count += 1
                    if fatal or (max_errors is not None and link.error_count >= max_errors):
                        link.state = 'invalid'
                        log.info('Link is marked as permanently invalid')

                if dry_run:
                    log.info('Dry run, not saving results')
                else:
                    link.save()

        else:
            log.info('No new links to scan')
