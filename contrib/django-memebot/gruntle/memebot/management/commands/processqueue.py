"""Processes the pending Link verification queue"""

from optparse import make_option
from django.core.management.base import NoArgsCommand, CommandError
from gruntle.memebot.utils.locking import LockError
from gruntle.memebot.scanner import process_queue

class Command(NoArgsCommand):

    help = __doc__
    option_list = (make_option('-n', dest='dry_run', default=False, action='store_true',
                               help="don't write results back to database"),
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, dry_run=False, **kwargs):
        try:
            process_queue(dry_run=dry_run)
        except LockError, exc:
            raise CommandError(exc)
