"""Rebuilds the RSS feed"""

from optparse import make_option
import sys
from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from gruntle.memebot.exceptions import LockError
from gruntle.memebot import rss

class Command(NoArgsCommand):

    help = __doc__

    option_list = (make_option('-q', dest='log_stream', default=sys.stderr, action='store_const', const=None,
                               help="don't log messages to console"),
                   make_option('-m', dest='max_links', type='int', help='max links in the feeds (default: per-feed)'),
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, log_stream=None, max_links=None, **kwargs):
        try:
            rss.rebuild_rss(log_stream=log_stream, max_links=max_links)
        except LockError, exc:
            raise CommandError(exc)
        except KeyboardInterrupt:
            print '\nCancelled'
