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
from django.conf import settings
from gruntle.memebot.models import Link
from gruntle.memebot.utils import get_yesno, human_readable_duration

try:
    import cPickle as pickle
except ImportError:
    import pickle

# constants
MAX_UNIQUE_DIRS = 1000
KEEP_DAYS = 14
KEEP_LINKS = 100

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

        # issue two queries: items to keep by <n> days or <n> links, choose the larger one & calculate what's left
        now, links = datetime.now(), Link.objects.filter(state='published')
        keep_count, keep = max([(q.count(), q) for q in (links.order_by('-created')[:keep_links],
                               links.filter(created__range=(now - timedelta(days=keep_days), now)))])
        cutoff = keep.aggregate(Min('created'))['created__min']
        archive = links.filter(created__lt=cutoff)[:20]
        archive_count = archive.count()

        # show some stats and get caller verification
        print 'Oldest created item to keep: ' + cutoff.ctime()
        print 'Number of published items to retain: %d' % keep_count
        print 'Number of items to archive: %d' % archive_count

        # get some verification first, this is destructive as hell.
        if archive_count and get_yesno('\nContinue (y/N)? ', default=False):

            # make unique directory inside the archive root
            base, fmt = ['memebot', 'archive', now.strftime('%Y%m%d')], '%%0%dd' % len(str(MAX_UNIQUE_DIRS - 1))
            if not os.path.exists(settings.ARCHIVE_DIR):
                os.makedirs(settings.ARCHIVE_DIR)
            for i in xrange(MAX_UNIQUE_DIRS):
                archive_dir = os.path.join(settings.ARCHIVE_DIR, '.'.join(base + [fmt % i]))
                try:
                    os.mkdir(archive_dir)
                    break
                except OSError, exc:
                    if exc.errno != errno.EEXIST:
                        raise
            else:
                raise OSError(errno.EEXIST, os.strerror(errno.EEXIST, archive_dir))

            # rudimentary meter
            def update(desc, i):
                sys.stderr.write('\r%s ... %d / %d' % (desc, i + 1, archive_count))
                sys.stderr.flush()

            print '\nBeginning dump ...'
            start = time.time()
            try:

                # dump the contents of the fields we're about to nuke
                for i, link in enumerate(archive.only('id', *FIELDS).values('id', *FIELDS)):
                    id = link.pop('id')
                    pickle_file = os.path.join(archive_dir, 'link-%08d.pkl' % id)
                    with open(pickle_file, 'wb') as fp:
                        pickle.dump(link, fp)
                    update('Dumping', i)
                print

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

                print '\nCreating %s ...' % os.path.basename(tar_file)
                with tarfile.open(tar_file, 'w') as tar:
                    for basedir, subdirs, filenames in os.walk(archive_dir):
                        for filename in filenames:
                            file = os.path.join(basedir, filename)
                            arcname = os.path.relpath(file, settings.ARCHIVE_DIR)
                            tar.add(file, arcname)

                shutil.rmtree(archive_dir)
                bz2_file = tar_file + '.bz2'

                print 'Creating %s ...' % os.path.basename(bz2_file)
                with bz2.BZ2File(bz2_file, 'w', 0, 9) as out_fp:
                    with open(tar_file, 'rb') as in_fp:
                        shutil.copyfileobj(in_fp, out_fp)

                os.remove(tar_file)
                print 'Archive is: ' + os.path.relpath(bz2_file, os.curdir)

            finally:
                print '\nFinished in ' + human_readable_duration(time.time() - start)
