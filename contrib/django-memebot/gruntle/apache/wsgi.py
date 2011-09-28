#!/usr/bin/env python

"""Apache+WSGI Bridge"""

import errno
import sys
import os

from django.core.handlers.wsgi import WSGIHandler

class MemeBot(WSGIHandler):

    """WSGI application for memebot"""

    def __init__(self, *args, **kwargs):
        settings_filename = kwargs.pop('settings_filename')

        # walk down, looking for settings file along the way
        project_dir = os.path.realpath(__file__)
        while True:
            project_dir = os.path.dirname(project_dir)
            if os.path.exists(os.path.join(project_dir, settings_filename)):
                break
            if project_dir in ('', os.sep):
                raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), settings_filename)

        install_dir, project_name = os.path.split(project_dir)

        # add both the install and project dir to path if not already there
        for import_dir in project_dir, install_dir:
            if import_dir not in sys.path:
                sys.path.append(import_dir)

        # configure application
        sys.dont_write_bytecode = True
        os.environ['DJANGO_SETTINGS_MODULE'] = '%s.%s' % (project_name, os.path.splitext(settings_filename)[0])
        super(Application, self).__init__(*args, **kwargs)


application = MemeBot()
