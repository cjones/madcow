"""Run pendings links thorugh scanner"""

from optparse import make_option
import sys
from django.core.management.base import NoArgsCommand, CommandError
from gruntle.memebot.utils.locking import LockError
from gruntle.memebot import scanner

class Command(NoArgsCommand):

    help = __doc__
    option_list = (make_option('-n', dest='dry_run', default=False, action='store_true',
                               help="don't write results back to database"),
                   make_option('-q', dest='log_stream', default=sys.stderr, action='store_const', const=None,
                               help="don't log messages to console"),
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, dry_run=False, log_stream=False, **kwargs):
        try:
            scanner.run(dry_run=dry_run, log_stream=log_stream)
        except LockError, exc:
            raise CommandError(exc)
