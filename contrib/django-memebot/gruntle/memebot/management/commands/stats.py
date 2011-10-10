"""Quickly get some statistics about link activity"""

from django.core.management.base import NoArgsCommand
from gruntle.memebot.utils import human_readable_duration
from gruntle.memebot.models import Link

class Command(NoArgsCommand):

    help = __doc__

    def handle_noargs(self, **kwargs):
        links = Link.objects.all().order_by('-created')
        pending_links = links.filter(state='new')
        new_links = pending_links.filter(error_count=0)
        deferred_links = pending_links.exclude(error_count=0)
        disabled_links = links.filter(state='disabled').order_by('-modified')
        archived_links = links.filter(state='archived').order_by('-modified')
        published_links = links.filter(state='published').order_by('-published')
        invalid_links = links.filter(state='invalid').order_by('-modified')

        link_count = links.count()
        pending_link_count = pending_links.count()
        new_link_count = new_links.count()
        deferred_link_count = deferred_links.count()
        disabled_link_count = disabled_links.count()
        archived_link_count = archived_links.count()
        published_link_count = published_links.count()
        invalid_link_count = invalid_links.count()

        print 'Link Counts'
        print '-----------'
        print 'Total: %d' % link_count
        print '    Pending: %d' % pending_link_count
        print '        New: %d' % new_link_count
        print '        Deferred: %d' % deferred_link_count
        print '    Disabled: %d' % disabled_link_count
        print '    Archived: %d' % archived_link_count
        print '    Published: %d' % published_link_count
        print '    Invalid: %d' % invalid_link_count
        print

        if link_count:
            last_link = links[0]
            self.print_link(last_link, 'Last Posted', 'created')
        else:
            last_link = None

        if published_link_count:
            last_published_link = published_links[0]
            if last_published_link != last_link:
                self.print_link(last_published_link, 'Last Published', 'published')
        else:
            last_published_link = None

        if deferred_link_count:
            deferred_link = deferred_links[0]
            if deferred_link not in (last_link, last_published_link):
                self.print_link(deferred_link, 'Last Deferred Link', 'modified', print_error=True)
        else:
            deferred_link = None

    @staticmethod
    def format_date(date):
        return '%s (%s ago)' % (date.strftime('%Y-%m-%d %H:%M:%S'), human_readable_duration(date, precision=2))

    @classmethod
    def print_link(cls, link, title=None, date_field=None, print_error=False):
        print title
        print '-' * len(title)
        print 'ID: %d' % link.id
        print 'URL: %s' % link.url
        print '%s: %s' % (date_field.capitalize(), cls.format_date(getattr(link, date_field)))
        print 'User: %s' % link.user.username
        print 'State: %s' % link.get_state_display()
        if link.state == 'published':
            if link.content is None:
                print 'Content: None'
            else:
                print 'Type: %s' % link.content_type
                print 'Size: %d' % len(link.content)
        else:
            print 'Errors: %d' % link.error_count
            if print_error and link.content_type == 'text/plain' and link.content:
                lines = link.content.strip().splitlines()
                if lines:
                    print 'Error: %s' % lines[-1]

        print
