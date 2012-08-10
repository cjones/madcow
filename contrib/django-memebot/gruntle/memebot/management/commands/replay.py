"""Replays logfiles from madcow as if the bot had seen the chatter in the first place"""

from itertools import imap

import datetime
import optparse
import sys
import os
import re

from django.core.management.base import BaseCommand, CommandError

from gruntle.memebot.utils import get_logger
from gruntle.memebot.models import Link
from gruntle.memebot.exceptions import OldMeme, BlackListError

USAGE_ERROR = 2
NO_LOGFILES = 4

_logfile_re = re.compile(r'^public-(.+?)-(\d{4})-(\d+)-(\d+)\.log$')
_logline_re = re.compile(r'^(\d{2}):(\d{2}):(\d{2})\s+(?:<(.+?)>|\*\s+(\S+))\s+(.+?)\s*$')
_url_re = re.compile(r'(https?://\S+)', re.IGNORECASE)

class Command(BaseCommand):

    help = __doc__
    args = '<file|dir> [file|dir ...]'

    @classmethod
    def iterlogs(cls, logdir):
        for dirname, subdirs, basenames in os.walk(logdir):
            for basename in basenames:
                if _logfile_re.search(basename) is not None:
                    yield os.path.join(dirname, basename)

    @classmethod
    def disable_auto_time(cls, log, *models):
        for model in models:
            for field in model._meta.fields:
                for key in 'auto_now', 'auto_now_add':
                    if getattr(field, key, False):
                        setattr(field, key, False)
                        log.info('Disabled %s.%s.%s', model._meta.object_name, field.name, key)

    def handle(self, *args, **kwargs):
        status = os.EX_OK
        log = get_logger('replay', stream=sys.stderr)
        try:
            if args:
                self.disable_auto_time(log, Link)
                links = Link.objects.order_by('-created')
                last_link = links[0].created if links else None

                logfiles = []
                for arg in args:
                    if os.path.isdir(arg):
                        it = self.iterlogs(arg)
                    else:
                        it = [arg]
                    for logfile in it:
                        basename = os.path.basename(logfile)
                        match = _logfile_re.search(basename)
                        if match is not None:
                            groups = match.groups()
                            logfiles.append((datetime.date(*imap(int, groups[1:])), '#' + groups[0], logfile))

                if logfiles:
                    logfiles.sort()
                    for created_date, channel, logfile in logfiles:
                        log.info('reading %s [%s, %s]', logfile, channel, created_date)
                        with open(logfile, 'rb') as fp:
                            for line in fp:
                                line = line.rstrip('\r\n')
                                match = _logline_re.search(line)
                                if match is not None:
                                    groups = match.groups()
                                    nick = groups[3] or groups[4]
                                    if nick.lower() != 'madcow':
                                        created_time = datetime.time(*imap(int, groups[:3]))
                                        created = datetime.datetime.combine(created_date, created_time)
                                        if last_link is not None and created <= last_link:
                                            log.warn('Skipping log record %s@%s: in the past', nick, created)
                                        else:
                                            for url in _url_re.findall(groups[5]):
                                                log.info('LINK: %s by %s @ %s', url, nick, created)
                                                try:
                                                    link = Link.objects.add_link(url, nick, channel, 'irc',
                                                                                created=created, modified=created)
                                                    log.info('Processed link to: %r', link)
                                                except OldMeme, old:
                                                    log.warn('link was an old meme: %s' % url)
                                                except BlackListError, exc:
                                                    log.warn('link is blacklisted: %s' % url)

                else:
                    status |= NO_LOGFILES
            else:
                status |= USAGE_ERROR
        except (SystemExit, KeyboardInterrupt, EOFError):
            raise
        except:
            log.exception('unhandled error during replay')
            raise
        if status != os.EX_OK:
            if status & USAGE_ERROR:
                self.print_help(sys.argv[0], 'replay')
            else:
                raise CommandError('replay did not finish cleanly: %d' % status)
