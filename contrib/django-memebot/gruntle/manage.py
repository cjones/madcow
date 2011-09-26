#!/usr/bin/python

import sys
import os

sys.dont_write_bytecode = True

from django.core.management import execute_manager, setup_environ
import settings

def main():
    args = sys.argv[1:]
    nargs = len(args)
    if nargs and args[0] == 'runserver':

        # turn on debugging dynamically
        setup_environ(settings)
        from django.conf import settings as real_settings
        real_settings.TEMPLATE_DEBUG = real_settings.DEBUG = True

        # mark ourselvs as a dev server
        os.environ['DEV_SERVER'] = 'true'

        # if not specified, use the binding in settings
        if nargs == 1:
            server_addr = getattr(settings, 'DEV_SERVER_ADDR', None)
            if server_addr:
                sys.argv.append(server_addr)

    execute_manager(settings)

if __name__ == '__main__':
    sys.exit(main())
