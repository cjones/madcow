import shelve
import sys
from django.core.management import BaseCommand
from django.contrib.auth.models import User
from gruntle.memebot.models import Link
from gruntle.memebot.exceptions import OldMeme
from gruntle.memebot.utils import DisableAutoTimestamps

class Command(BaseCommand):

    args = '<dbfile>'
    help = 'Import old memebot database'

    def handle(self, db_file, **kwargs):
        db = shelve.open(db_file)
        posts = sorted(db['urls'].itervalues(), key=lambda post: post['date'])
        size = len(posts)
        with DisableAutoTimestamps(Link):

            for i, post in enumerate(posts):
                date = post['date']
                try:
                    link = Link.objects.add_link(
                            post['orig'], post['nick'], '#hugs', 'irc', created=date, modified=date)

                except OldMeme, exc:
                    link = exc.link
                    print >> sys.stderr, '%s\rFailed to add %r because %r exists' % (' ' * 72, post, link)
                sys.stderr.write('Importing: %d / %d\r' % (i + 1, size))
                sys.stderr.flush()

            for nick, data in db['nicks'].iteritems():
                try:
                    user = User.objects.get(username=nick)
                except User.DoesNotExist:
                    continue
                profile = user.get_profile()
                profile.posted_new = data['new']
                profile.posted_old = data['old']
                profile.reposts = data['credit']
                profile.save()
