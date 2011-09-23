"""Watch URLs in channel, punish people for living under a rock"""

def setup_environ():
    import sys
    from madcow.conf import settings
    project_root = getattr(settings, 'DJMEMEBOT_PROJECT_ROOT', None)
    if project_root is None:
        raise ImportError('djmemebot is not configured: must set DJMEMEBOT_PROJECT_ROOT in settings.py')
    if project_root not in sys.path:
        sys.path.append(project_root)
    try:
        from gruntle import settings as project_settings
    except ImportError:
        raise ImportError("couldn't import django settings file, check DJMEMEBOT_PROJECT_ROOT")
    try:
        from django.core.management import setup_environ
    except ImportError:
        raise ImportError('django is not installed')
    setup_environ(project_settings)

setup_environ()
del setup_environ

import random
import re

from gruntle.memebot.exceptions import OldMeme
from gruntle.memebot.models import Link, UserProfile

from madcow.util import Module
from madcow.util.textenc import *

class Main(Module):

    pattern = Module._any
    allow_threading = False
    priority = 10
    terminate = False
    require_addressing = False
    help = 'score [name | x - y] - get memescore'

    url_re = re.compile(r'(https?://\S+)', re.IGNORECASE)
    score_request_re = re.compile(r'^\s*score(?:(?:\s+|[:-]+\s*)(\S+?)(?:\s*-\s*(\S+))?)?\s*$', re.I)

    riffs = ['OLD MEME ALERT!',
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

    @staticmethod
    def getint(val, default=None):
        try:
            return int(val)
        except StandardError:
            return default

    def response(self, nick, args, kwargs):
        message = encode(args[0])

        if kwargs['addressed']:
            match = self.score_request_re.search(message)
            if match is not None:
                start = self.getint(match.group(1), 1)
                end = self.getint(match.group(2), start + 9)
                profiles = UserProfile.objects.get_by_score()[start - 1: end]
                if profiles:
                    return u', '.join(u'#%d: %s (%d)' % ((start + i), profile.user.username, profile.score)
                                      for i, profile in enumerate(profiles))
                else:
                    return u'Out of range, there are only %d users, jeez.' % UserProfile.objects.count()

        match = self.url_re.search(message)
        if match is not None:
            url = decode(match.group(1))
            try:
                link = Link.objects.add_link(url, nick.lower(), kwargs['channel'].lower(), 'irc')
            except OldMeme, exc:
                return u'%s First posted by %s on %s' % (
                        random.choice(self.riffs),
                        exc.link.user.username,
                        exc.link.created.strftime('%Y-%m-%d %H:%M:%S'))
