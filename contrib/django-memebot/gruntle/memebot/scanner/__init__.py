#!/usr/bin/env python

if __name__ == '__main__':
    import os
    args = ['./manage.py', 'processqueue', '-n']
    os.chdir('/home/cjones/proj')
    os.execvp(args[0], args)
    os._exit(1)

"""Core handler for processing/scanning Link objects"""

import datetime
from django.conf import settings
from gruntle.memebot.utils import TrapError, TrapErrors, locking, text, plural, get_logger
from gruntle.memebot.utils.browser import Browser
from gruntle.memebot.decorators import logged
from gruntle.memebot.models import Link

@logged('process-queue', append=True)
def process_queue(log, user_agent=None, max_links=None, max_read=None, max_errors=None, dry_run=False):
    """Process the pending link queue"""
    with locking.Lock('process-queue', 0):
        if max_links is None:
            max_links = settings.PROCESSOR_MAX_LINKS
        links = Link.objects.filter(state='new').order_by('created')
        if max_links is not None:
            links = links[:max_links]
        num_links = links.count()
        if num_links:
            if user_agent is None:
                user_agent = settings.PROCESSOR_USER_AGENT
            if max_read is None:
                max_read = settings.PROCESSOR_MAX_READ
            if max_errors is None:
                max_errors = settings.PROCESSOR_MAX_ERRORS
            browser = Browser(user_agent=user_agent)
            for i, link in enumerate(links):
                log.info('[%d/%d] Processing: %s', i + 1, num_links, link.url)
                fatal = False
                try:
                    with TrapErrors():
                        response = browser.open(link.url, max_read=max_read)
                        if response.code == 200:
                            publish = True
                            link.resolved_url = response.real_url
                            link.mime_type = response.mime_type
                            '''
                        # print text.encode(u', '.join(text.format(u'%s=%r', key, getattr(response, key, None))
                        #                              for key in ('is_valid', 'redirected', 'mime_type', 'code',
                        #                                          'msg', 'orig_url', 'real_url', 'data_type')))

                            # content_type, content, title
    LINK_CONTENT_TYPES = [('image', 'Image Data'),           # content is raw image data to be displayed in-line
                          ('summary', 'Summary Text'),       # content is a text paragraph from an article/blog/essay
                          ('rendered', 'Pre-Rendered HTML'), # hint from scanner, indicates content is already rendered
                          ('error', 'Error Message')]        # why this link could not validate, text
                            '''
                        else:
                            publish = False
                            link.content_type = 'error'
                            link.content = response.msg
                            if response.code == 404:
                                fatal = True

                except TrapError, exc:
                    link.content_type = 'error'
                    link.content = exc
                    publish = False

                if publish:
                    link.state = 'published'
                    link.error_count = 0
                    link.published = datetime.datetime.now()
                else:
                    link.error_count += 1
                    if fatal or (max_errors is not None and link.error_count >= max_errors):
                        link.state = 'invalid'

                if not dry_run:
                    link.save()

        else:
            log.info('No new links to process')
