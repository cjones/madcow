"""Rebuilds the RSS feed"""

from optparse import make_option
import sys
from django.core.management.base import BaseCommand, CommandError
from mezzanine.conf import settings
from memebot.exceptions import LockError
from memebot import feeds

class Command(BaseCommand):

    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument('-q', '--quiet', dest='log_stream', default=sys.stderr, action='store_const', const=None)
        parser.add_argument('-f', '--force', default=False, action='store_true')

    def handle(self, log_stream=None, force=False, **options):
        try:
            feeds.run(log_stream=log_stream, force=force)
        except LockError as exc:
            raise CommandError(exc)
        except KeyboardInterrupt:
            print('\nCancelled')

