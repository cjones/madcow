"""Auto-configuring Django-WSGI handler"""

import errno
import sys
import os

import django.core.handlers.wsgi

def auto_configure_wsgi(settings_filename='settings.py'):
    """Automatically configure WSGI"""

    # walk backwards looking for a settings file in each dir
    project_dir = os.path.realpath(__file__)
    while True:
        project_dir = os.path.dirname(project_dir)
        if os.path.exists(os.path.join(project_dir, settings_filename)):
            break
        elif project_dir in ('', os.sep):
            raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), settings_filename)

    install_dir, project_name = os.path.split(project_dir)

    # add both the install and project dir to path if not already there
    for import_dir in project_dir, install_dir:
        if import_dir not in sys.path:
            sys.path.append(import_dir)

    # return configured application
    sys.dont_write_bytecode = True
    os.environ['DJANGO_SETTINGS_MODULE'] = '%s.%s' % (project_name, os.path.splitext(settings_filename)[0])
    return django.core.handlers.wsgi.WSGIHandler()


application = auto_configure_wsgi()
