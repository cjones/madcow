"""Resets publish status of links"""

from django.core.management import BaseCommand, CommandError
from django.db import connection, transaction
from gruntle.memebot.models import Link, SerializedData

class Command(BaseCommand):

    args = '[state]'
    help = 'Reset status of links'

    def handle(self, *args, **kwargs):
        nargs = len(args)
        if nargs == 0:
            state = 'new'
        elif nargs == 1:
            state = args[0]
        else:
            raise CommandError('invalid arguments, -h for help')

        updates = {'state': state,
                   'error_count': 0,
                   'resolved_url': None,
                   'content_type': None,
                   'content': None,
                   'title': None,
                   'published': None,
                   'publish_id': None,
                   'scanner': None,
                   'attr_storage': None}

        sql = []
        params = []
        for field, value in updates.iteritems():
            sql.append(field + ' = %s')
            params.append(value)

        cursor = connection.cursor()
        cursor.execute('UPDATE %s SET %s;' % (Link._meta.db_table, ', '.join(sql)), tuple(params))
        transaction.commit_unless_managed()

        sdata = SerializedData.objects.all()
        if sdata.count():
            print 'Deleting %d serialized data items' % sdata.count()
            sdata.delete()

        print 'Reset complete'
