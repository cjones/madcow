"""Handle import from old shelve db"""

import collections
import datetime
import sys
import os
import re

from django.core.management import BaseCommand, CommandError
from django.contrib.auth.models import User

from gruntle.memebot.models import Link
from gruntle.memebot.exceptions import OldMeme
from gruntle.memebot.utils import DisableAutoTimestamps, text

log_file_re = re.compile(r'^public-(.+?)-(\d{4})-(\d{2})-(\d{2})\.log$', re.IGNORECASE)
url_re = re.compile(r'(https?://\S+)', re.IGNORECASE)
post_re = re.compile(r'^\s*(\d{2}):(\d{2}):(\d{2})\s*<\s*[@+]*(.+?)\s*>\s*')

Post = collections.namedtuple('Post', 'nick hour minute second')

class Command(BaseCommand):

    args = '<log> [log ...]'
    help = 'Scrape links from IRC logs'

    def handle(self, *args, **kwargs):
        if not args:
            raise CommandError('invalid arguments, -h for help')

        log_files = []
        for log_file in args:
            log_filename = os.path.basename(log_file)
            match = log_file_re.search(log_filename)
            if match is None:
                print >> sys.stderr, text.encode(text.format("Don't recognize filename structure: %r", log_filename))
            else:
                groups = list(match.groups())
                channel = groups.pop(0)
                if not channel.startswith('#'):
                    channel = '#' + channel
                date = datetime.date(*map(int, groups))
                log_files.append((date, channel, log_file))
        log_files.sort()

        with DisableAutoTimestamps(Link):

            for date, channel, log_file in log_files:
                with open(log_file, 'r') as fp:
                    for line in fp:
                        line = text.sencode(text.chomp(line))
                        if isinstance(line, unicode):
                            raise ValueError('WTF')
                        if line is not None:
                            post = None
                            for url in url_re.findall(line):
                                if post is None:
                                    match = post_re.search(line)
                                    if match is None:
                                        raise ValueError(text.format("Couldn't find nick from %r", line))
                                    post = Post(nick=text.decode(match.group(4)),
                                                hour=text.cast(match.group(1)),
                                                minute=text.cast(match.group(2)),
                                                second=text.cast(match.group(3)))

                                posted = datetime.datetime(date.year, date.month, date.day,
                                                           post.hour, post.minute, post.second)


                                try:
                                    Link.objects.add_link(url, post.nick, channel, 'irc',
                                                          created=posted, modified=posted)

                                except OldMeme, exc:
                                    print text.encode(text.format('OLD: [%s] <%s:%s> {%s} %s',
                                                                  posted.strftime('%Y-%m-%d %H:%M:%S'),
                                                                  post.nick, channel, exc.link.user.username, url))

