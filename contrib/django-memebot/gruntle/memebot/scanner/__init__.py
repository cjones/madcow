#!/usr/bin/env python

if __name__ == '__main__':
    import os
    args = ['./manage.py', 'processqueue', '-n']
    os.chdir('/home/cjones/proj')
    os.execvp(args[0], args)
    os._exit(1)

"""Core handler for processing/scanning Link objects"""

import datetime

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

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
                        if response.is_valid:
                            publish = True
                            link.resolved_url = response.real_url

                            if response.data_type == 'image':
                                link.mime_type = 'image/png'
                                link.content_type = 'image'
                                fileobj = stringio.StringIO()
                                response.data.save(fileobj, 'PNG')
                                link.content = fileobj.getvalue()
                                # summary, rendered
                            else:
                                link.mime_type = response.mime_type

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
                    link.publish(commit=False)
                else:
                    link.error_count += 1
                    if fatal or (max_errors is not None and link.error_count >= max_errors):
                        link.state = 'invalid'

                if not dry_run:
                    link.save()

        else:
            log.info('No new links to process')
