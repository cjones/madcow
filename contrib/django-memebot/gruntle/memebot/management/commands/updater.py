"""Automatically scans for new links and rebuilds RSS"""

from optparse import make_option

import time
import sys

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from gruntle.memebot.exceptions import TrapError, TrapErrors
from gruntle.memebot.decorators import locked, logged
from gruntle.memebot import scanner, feeds

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
        except TrapError, exc:
            raise CommandError(exc.args[1])

    @logged('updater', append=True, method=True)
    @locked('updater', 0)
    def run(self, interval):
        self.log.info('Running...')
        last_update = 0
        while True:
            now = time.time()
            elapsed = now - last_update
            need = interval - elapsed
            if need > 0:
                time.sleep(need)
            try:
                with TrapErrors():
                    scanner.run(log_stream=sys.stdout)
                    feeds.run(log_stream=sys.stdout, force=False)
            except TrapError, exc:
                self.log.error('Processing Error', exc_info=exc.args)
            last_update = now
