"""Watch URLs in channel, punish people for living under a rock"""

import random
import sys
import re
import os

from madcow.conf import settings
from madcow.util import Module
from madcow.util.text import encode, decode

DEFAULT_INSULTS = ['OLD MEME ALERT!',
                   'omg, SO OLD!',
                   'Welcome to yesterday.',
                   'been there, done that.',
                   'you missed the mememobile.',
                   'oldest. meme. EVAR.',
                   'jesus christ you suck.',
                   'you need a new memesource, bucko.',
                   'that was funny the first time i saw it.',
                   'new to the internet?',
                   'i think that came installed with the internet.',
                   'are you serious?',
                   'CHOO!! CHOO!! ALL ABOARD THE OLD MEME TRAIN!']

url_re = re.compile(r'(https?://\S+)', re.IGNORECASE)
score_request_re = re.compile(r'^\s*score(?:(?:\s+|[:-]+\s*)(\S+?)(?:\s*-\s*(\S+))?)?\s*$', re.I)

class Memebot(object):

    """Interface to django-memebot"""

    def __init__(self, settings_file, logger, insults=None):
        if insults is None:
            insults = DEFAULT_INSULTS
        self.insults = insults
        self.log = logger
        settings_file = os.path.realpath(settings_file)
        project_dir, settings_filename = os.path.split(settings_file)
        settings_name = os.path.splitext(settings_filename)[0]
        install_dir, project_name = os.path.split(project_dir)
        for package_dir in project_dir, install_dir:
            while package_dir in sys.path:
                sys.path.remove(package_dir)
            sys.path.insert(0, package_dir)
        os.environ['DJANGO_SETTINGS_MODULE'] = '%s.%s' % (project_name, settings_name)
        sys.dont_write_bytecode
        import django.db

    def get_scores(self, range=None, name=None):
        from gruntle.memebot.models import UserProfile
        if name is not None:
            name = name.lower()
        profiles = [(i + 1, profile) for i, profile in enumerate(UserProfile.objects.get_by_score())
                    if (range is not None and i >= range[0] and i <= range[1]) or
                       (profile.user.username.lower() == name)]
        return u', '.join(u'#%d: %s (%d)' % (rank, profile.user.username, profile.score) for rank, profile in profiles)

    def process_url(self, url, nick, source_name):
        from gruntle.memebot.models import Link
        from gruntle.memebot.exceptions import OldMeme, BlackListError
        try:
            link = Link.objects.add_link(url, nick.lower(), source_name.lower(), settings.PROTOCOL)
            self.log.info('%s posted a link to %s: %r', nick, source_name, link)
        except OldMeme, exc:
            return '%s First posted by %s on %s' % (random.choice(self.insults),
                                                    exc.link.user.username,
                                                    exc.link.created.ctime())
        except BlackListError, exc:
            self.log.warn('%s posted a link to %s that was blacklisted: %s', nick, source_name, exc)


class MemebotModule(Module):

    """Madcow module for memebot"""

    pattern = Module._any
    allow_threading = False
    priority = 10
    terminate = False
    require_addressing = False
    help = 'score [name | x - y] - get memescore'

    def __init__(self, *args, **kwargs):
        super(Main, self).__init__(*args, **kwargs)
        self.memebot = Memebot(settings.DJMEMEBOT_SETTINGS_FILE, logger=self.log, insults=settings.OLD_MEME_INSULTS)

    def response(self, nick, args, kwargs):
        message = encode(args[0])
        if kwargs['addressed']:
            match = score_request_re.search(message)
            if match is not None:
                start, end = match.groups()

                # asking for a username
                if end is None and start is not None:
                    return self.memebot.get_scores(name=start)
                start = ((int(start) if start is not None and start.isdigit() else None) or 1) - 1
                end = ((int(end) if end is not None and end.isdigit() else None) or start + 10) - 1
                if start < 0:
                    start = 0
                if end < start:
                    end = start
                return self.memebot.get_scores(range=(start, end))

        match = url_re.search(message)
        if match is not None:
            url = decode(match.group(1))
            return self.memebot.process_url(url, nick, kwargs['channel'])


Main = MemebotModule
