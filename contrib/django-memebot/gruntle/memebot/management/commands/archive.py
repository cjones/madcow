"""Archives stored content, freeing up db space"""

from datetime import datetime, timedelta
from optparse import make_option
import tarfile
import shutil
import errno
import time
import bz2
import sys
import os

from django.core.management.base import NoArgsCommand, CommandError
from django.db.models import Min
from mezzanine.conf import settings
from memebot.models import Link
from memebot.utils import get_yesno, human_readable_duration

try:
    import pickle as pickle
except ImportError:
    import pickle

# constants
MAX_UNIQUE_DIRS = 1000
KEEP_DAYS = 14
KEEP_LINKS = 512

# fields to dump from archived Links
FIELDS = 'resolved_url', 'content_type', 'content', 'title', 'published', 'publish_id', 'scanner', 'attr_storage'

class Command(NoArgsCommand):

    help = __doc__

    option_list = (make_option('-d', '--keep-days', metavar='<days>', type='int', default=KEEP_DAYS,
                               help='minimum days of published content to retain (default %default)'),
                   make_option('-l', '--keep-links', metavar='<num>', type='int', default=KEEP_LINKS,
                               help='minimum # of links to retain (default: %default)')
                   ) + NoArgsCommand.option_list

    def handle_noargs(self, keep_days=KEEP_DAYS, keep_links=KEEP_LINKS, **kwargs):

        now = datetime.now()
        cutoff = now - timedelta(days=keep_days)

        published_links = Link.objects.filter(state='published').order_by('-created')
        keep1 = published_links[:keep_links]
        keep2 = published_links.filter(created__gte=cutoff)
        keep_ids = {link.id for qs in [keep1, keep2] for link in qs}
        archive = published_links.exclude(id__in=keep_ids)
        archive_count = archive.count()

        print('Number of published items to retain: %d' % len(keep_ids))
        print('Number of published items to archive: %d' % archive_count)

        # get some verification first, this is destructive as hell.
        if archive_count and get_yesno('\nContinue (y/N)? ', default=False):

            # make unique directory inside the archive root
            base, fmt = ['memebot', 'archive', now.strftime('%Y%m%d')], '%%0%dd' % len(str(MAX_UNIQUE_DIRS - 1))
            if not os.path.exists(settings.ARCHIVE_DIR):
                os.makedirs(settings.ARCHIVE_DIR)
            for i in range(MAX_UNIQUE_DIRS):
                archive_dir = os.path.join(settings.ARCHIVE_DIR, '.'.join(base + [fmt % i]))
                try:
                    os.mkdir(archive_dir)
                    break
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            else:
                raise OSError(errno.EEXIST, os.strerror(errno.EEXIST, archive_dir))

            # rudimentary meter
            def update(desc, i):
                sys.stderr.write('\r%s ... %d / %d' % (desc, i + 1, archive_count))
                sys.stderr.flush()

            print('\nBeginning dump ...')
            start = time.time()
            try:

                # dump the contents of the fields we're about to nuke
                for i, link in enumerate(archive.only('id', *FIELDS).values('id', *FIELDS)):
                    id = link.pop('id')
                    pickle_file = os.path.join(archive_dir, 'link-%08d.pkl' % id)
                    with open(pickle_file, 'wb') as fp:
                        pickle.dump(link, fp)
                    update('Dumping', i)
                print()

                # nuke 'em
                for i, link in enumerate(archive.only('id')):
                    link.state = 'archived'
                    for field in FIELDS:
                        setattr(link, field, None)
                    link.save()
                    update('Cleaning Content', i)

                # compress archive dir
                tar_file = archive_dir + '.tar'
                if os.path.exists(tar_file):
                    os.remove(tar_file)

                print('\nCreating %s ...' % os.path.basename(tar_file))
                with tarfile.open(tar_file, 'w') as tar:
                    for basedir, subdirs, filenames in os.walk(archive_dir):
                        for filename in filenames:
                            file = os.path.join(basedir, filename)
                            arcname = os.path.relpath(file, settings.ARCHIVE_DIR)
                            tar.add(file, arcname)

                shutil.rmtree(archive_dir)
                bz2_file = tar_file + '.bz2'

                print('Creating %s ...' % os.path.basename(bz2_file))
                with bz2.BZ2File(bz2_file, 'w', 0, 9) as out_fp:
                    with open(tar_file, 'rb') as in_fp:
                        shutil.copyfileobj(in_fp, out_fp)

                os.remove(tar_file)
                print('Archive is: ' + os.path.relpath(bz2_file, os.curdir))

            finally:
                print('\nFinished in ' + human_readable_duration(time.time() - start))
