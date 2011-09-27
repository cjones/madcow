"""Rebuilds the RSS feed"""

from optparse import make_option
import sys

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from gruntle.memebot.utils.locking import LockError
from gruntle.memebot import rss

class Command(NoArgsCommand):

    help = __doc__
    option_list = (#make_option('-n', dest='dry_run', default=False, action='store_true',
                   #            help="don't write results back to database"),
                   make_option('-q', dest='log_stream', default=sys.stderr, action='store_const', const=None,
                               help="don't log messages to console"),
                   #make_option('-m', dest='max_links', default=settings.SCANNER_MAX_LINKS, type='int',
                   #            help='max links to fetch (default: %default)')
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, log_stream=None, **kwargs):
        try:
            rss.rebuild_rss(log_stream=log_stream)
        except LockError, exc:
            raise CommandError(exc)
        except KeyboardInterrupt:
            print '\nCancelled'
