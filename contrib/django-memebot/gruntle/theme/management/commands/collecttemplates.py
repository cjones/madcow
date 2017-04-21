from __future__ import unicode_literals

from mezzanine.conf import settings

from mezzanine.core.management.commands.collecttemplates import Command as BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        ret = super(Command, self).add_arguments(parser)
        parser.add_argument('-A', '--all-apps', default=False, action='store_true',
                            help='copy templates from all installed apps')
        return ret

    def handle(self, *apps, **options):
        apps = list(apps)
        if options.pop('all_apps', False):
            apps.extend(settings.INSTALLED_APPS)
        apps = tuple(sorted(set(apps), key=apps.index))
        return super(Command, self).handle(*apps, **options)

