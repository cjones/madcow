"""Rebuilds the RSS feed"""

from optparse import make_option
import sys

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from gruntle.memebot.utils.locking import LockError
from gruntle.memebot import rss

class Command(NoArgsCommand):

    help = __doc__
    option_list = (make_option('-q', dest='log_stream', default=sys.stderr, action='store_const', const=None,
                               help="don't log messages to console"),
                   make_option('-m', dest='max_links', default=settings.RSS_MAX_LINKS, type='int',
                               help='max links to process at once (default: %default)'),
                   make_option('-n', dest='num_links', default=settings.RSS_NUM_LINKS, type='int',
                               help='number of links in the feed (default: %default)'),
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, log_stream=None, max_links=None, num_links=None, **kwargs):
        try:
            rss.rebuild_rss(log_stream=log_stream, max_links=max_links, num_links=num_links)
        except LockError, exc:
            raise CommandError(exc)
        except KeyboardInterrupt:
            print '\nCancelled'
