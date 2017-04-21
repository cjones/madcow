"""Rebuilds the RSS feed"""

from optparse import make_option
import sys
from django.core.management.base import NoArgsCommand, CommandError
from mezzanine.conf import settings
from memebot.exceptions import LockError
from memebot import feeds

class Command(NoArgsCommand):

    help = __doc__

    option_list = (make_option('-q', dest='log_stream', default=sys.stderr, action='store_const', const=None,
                               help="don't log messages to console"),
                   make_option('-f', dest='force', default=False, action='store_true', help='force rss generation'),
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, log_stream=None, force=False, **kwargs):
        try:
            feeds.run(log_stream=log_stream, force=force)
        except LockError as exc:
            raise CommandError(exc)
        except KeyboardInterrupt:
            print('\nCancelled')
