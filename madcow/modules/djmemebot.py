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

    # def get_scores(self):
    #     scores = [(nick, self.get_score_for_nick(nick)) for nick, author in self.db['nicks'].iteritems()]
    #     return sorted(scores, key=lambda item: item[1], reverse=True)
    # def score_response(self, x, y):
    #     scores = self.get_scores()
    #     size = len(scores)
    #     if x is None:
    #         scores = scores[:10]
    #         x = 1
    #     elif x.isdigit():
    #         x = int(x)
    #         if x == 0:
    #             x = 1
    #         if x > size:
    #             x = size
    #         if y and y.isdigit():
    #             y = int(y)
    #             if y > size:
    #                 y = size
    #             scores = scores[x-1:y]
    #         else:
    #             scores = [scores[x-1]]
    #     else:
    #         for i, data in enumerate(scores):
    #             name, score = data
    #             if name.lower() == x.lower():
    #                 scores = [scores[i]]
    #                 x = i+1
    #                 break
    #     out = []
    #     for i, data in enumerate(scores):
    #         name, score = data
    #         out.append('#%s: %s (%s)' % (i + x, name, score))
    #     return ', '.join(out)

    # def __del__(self):
    #     self.db.close()
    #     self.queue.put(None)
    #    def get_score(self, username):
    #        username = username.lower()
    #        try:
    #            user = Alias.objects.get(username=username).user
    #        except Alias.DoesNotExist:
    #            try:
    #                user = User.objects.get(username=username)
    #            except User.DoesNotExist:
    #                user = None
    #
    #        if user is None:
    #            score = 0
    #        else:
    #            profile = user.get_profile()
    #            score = profile.score
    #        return score
    #
