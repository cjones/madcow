"""Run pendings links thorugh scanner"""

from optparse import make_option
import sys
from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from gruntle.memebot.exceptions import LockError
from gruntle.memebot import scanner

try:
    import multiprocessing as mp
    DEFAULT_NUM_WORKERS = mp.cpu_count()
except ImportError:
    mp = None
    DEFAULT_NUM_WORKERS = None

class Command(NoArgsCommand):

    help = __doc__

    option_list = (make_option('-n', dest='dry_run', default=False, action='store_true',
                               help="don't write results back to database"),
                   make_option('-q', dest='log_stream', default=sys.stderr, action='store_const', const=None,
                               help="don't log messages to console"),
                   make_option('-m', dest='max_links', default=settings.SCANNER_MAX_LINKS, type='int',
                               help='max links to fetch (default: %default)'),
                   make_option('-f', dest='fork', default=False, action='store_true', help='run multiple workers'),
                   make_option('-w', dest='num_workers', default=DEFAULT_NUM_WORKERS, type='int',
                               help='number of workers when forking (default: auto)'),
                   )

    if mp is not None:
        option_list = option_list + (
                make_option('-M', dest='use_multiprocessing', default=False, action='store_true',
                    help='use multiprocessing instead of native threads'),
                )

    option_list = option_list + NoArgsCommand.option_list

    def handle_noargs(self, max_links=None, dry_run=False, log_stream=None, fork=False,
                      num_workers=None, use_multiprocessing=True, **kwargs):
        try:
            scanner.run(max_links=max_links, dry_run=dry_run, log_stream=log_stream, fork=fork,
                        num_workers=num_workers, use_multiprocessing=use_multiprocessing)
        except LockError, exc:
            raise CommandError(exc)
        except KeyboardInterrupt:
            print '\nCancelled'
