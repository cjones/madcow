"""Tests the scanner with an arbitrary URL without recording the results"""

from optparse import make_option

import sys

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from gruntle.memebot.exceptions import TrapError, TrapErrors
from gruntle.memebot.utils import get_logger, ipython
from gruntle.memebot.utils.browser import Browser

class Command(BaseCommand):

    help = __doc__
    args = '<url> [url ...]'

    option_list = (
            make_option('-s', '--scanner', metavar='<name>', help='scanner to test'),
            make_option('-a', '--user-agent', metavar='<agent>', default=settings.SCANNER_USER_AGENT,
                        help='use specified user agent or preset (default: %default)'),
            make_option('-t', '--timeout', metavar='<seconds>', type='int', default=settings.SCANNER_TIMEOUT,
                        help='network timeout for HTTP request (default: %default)'),
            make_option('-m', '--max-read', metavar='<bytes>', type='int', default=settings.SCANNER_MAX_READ,
                        help='maximum read size (default: %default)'),
            make_option('-i', '--ipython', dest='do_ipython', default=False, action='store_true',
                        help='open an ipython shell after link is processed'),
            ) + BaseCommand.option_list

    def handle(self, *urls, **kwargs):
        if not urls:
            raise CommandError('No URLs specified')

        scanner = kwargs.pop('scanner', None)
        if scanner is None:
            raise CommandError('Must specify a scanner to use')

        try:
            module = __import__('gruntle.memebot.scanner.' + scanner, globals(), locals(), ['scanner'])
        except ImportError, exc:
            raise CommandError("Couldn't import %s: %s" % (scanner, exc))

        try:
            handler = module.scanner
        except AttributeError:
            raise CommandError('No scanner is configured there')

        user_agent = kwargs.pop('user_agent', None)
        if user_agent is None:
            user_agent = settings.SCANNER_USER_AGENT

        timeout = kwargs.pop('timeout', None)
        if timeout is None:
            timeout = settings.SCANNER_TIMEOUT

        max_read = kwargs.pop('max_read', None)
        if max_read is None:
            max_read = settings.SCANNER_MAX_READ

        do_ipython = kwargs.pop('do_ipython', False)

        browser = Browser(user_agent=user_agent, timeout=timeout, max_read=max_read)
        log = get_logger('scantest', append=True, stream=sys.stdout)
        for url in urls:
            try:
                with TrapErrors():
                    response = browser.open(url, follow_meta_redirect=True)
                    if not response.is_valid:
                        raise ValueError('Response invalid')

                    result = handler.scan(response, log, browser)

                    log.info('Success: %r', result)

            except TrapError, exc:
                log.error('Problem parsing %r', url, exc_info=exc.args)

            if do_ipython:
                ipython()
