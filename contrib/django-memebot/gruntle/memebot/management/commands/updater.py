"""Automatically scans for new links and rebuilds RSS"""

from optparse import make_option

import time
import sys

from django.core.management.base import NoArgsCommand, CommandError
from mezzanine.conf import settings

from memebot.utils import human_readable_duration
from memebot.exceptions import TrapError, TrapErrors
from memebot.decorators import locked, logged
from memebot import scanner, feeds

class Command(NoArgsCommand):

    help = __doc__
    option_list = (
            make_option('-i', '--interval', metavar='<seconds>', type='int', default=settings.UPDATER_INTERVAL,
                        help='how often to process (default: %default)'),
            ) + NoArgsCommand.option_list

    def handle_noargs(self, interval=None, **kwargs):
        if interval is None:
            interval = settings.UPDATER_INTERVAL
        try:
            with TrapErrors():
                self.run(interval, log_stream=sys.stdout)
        except KeyboardInterrupt:
            raise CommandError('Interrupted')
        except TrapError as exc:
            raise CommandError(exc.args[1])

    @logged('updater', append=True, method=True)
    @locked('updater', 0)
    def run(self, interval):
        self.log.info('Starting updater service')
        last_update = 0
        while True:
            now = time.time()
            sleep = interval + last_update - now
            if sleep > 0:
                self.log.info('Sleeping for %s', human_readable_duration(sleep))
                time.sleep(sleep)
            try:
                with TrapErrors():
                    scanner.run(logger=self.log)
                    feeds.run(logger=self.log, force=False)
            except TrapError as exc:
                self.log.error('Processing Error', exc_info=exc.args)
            last_update = now
