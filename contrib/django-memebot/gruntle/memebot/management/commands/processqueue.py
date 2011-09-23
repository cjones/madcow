"""Processes the pending Link verification queue"""

from django.core.management.base import NoArgsCommand
from gruntle.memebot.scanner import process_queue

class Command(NoArgsCommand):

    help = __doc__

    def handle_noargs(self, **kwargs):
        process_queue()
