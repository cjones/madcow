"""Bounce last published links so they can be rescanned. Drops metadata."""

from optparse import make_option
import sys
from django.core.management.base import NoArgsCommand, CommandError
from mezzanine.conf import settings
from memebot.models import Link

MIN_LINKS = 25
DATEFMT = '%Y-%m-%d %H:%M:%S'

def get_max_links():
    from memebot.feeds import get_feeds
    return max([getattr(f[1], 'max_links', 0) for f in get_feeds()] + [MIN_LINKS])


class Command(NoArgsCommand):

    help = __doc__

    option_list = (make_option('-c', dest='count', default=get_max_links(), type='int',
                               help="number of links to bounce [%default]"),
                   make_option('-r', dest='reset', default=False, action='store_true',
                               help="also reset published date/id (normally retained)"),
                   make_option('-n', dest='dry_run', default=False, action='store_true',
                               help="don't write to db, only show matching links"),
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, count=None, reset=False, dry_run=False, **kwargs):
        if count is None:
            count = get_max_links()
        if count <= 0:
            raise CommandError('must specify at least one for bouncing')
        links = Link.objects.all()
        pending_count = links.filter(state='new').count()
        if pending_count >= count:
            raise CommandError('there are already %d links pending scan' % pending_count)
        elif pending_count > 0:
            count -= pending_count
            print('%d links already pending, reducing count to %d bounces' % (pending_count, count), file=sys.stderr)
        pub_links = links.filter(state='published').order_by('-published')[:count]
        nlinks = pub_links.count()
        for i, link in enumerate(pub_links):
            if dry_run:
                verb = 'Would reset'
            else:
                verb = 'Reset'
                link.state = 'new'
                link.error_count = 0
                link.resolved_url = None
                link.content_type = None
                link.content = None
                link.title = None
                link.scanner = None
                link.attr_storage = None
                if reset:
                    link.published = None
                    link.publish_id = None
                link.save()
            print('[%d/%d] %s: %s <%s> %s' % (
                    i + 1,
                    nlinks,
                    verb,
                    link.created.strftime(DATEFMT),
                    link.user.username,
                    link.url,
                    ))
