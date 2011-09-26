#!/usr/bin/python

import sys
import os

sys.dont_write_bytecode = True
os.environ['DEV_SERVER'] = 'true'

from django.core.management import execute_manager, setup_environ
import settings

def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'runserver':
        sys.argv.append(settings.DEV_SERVER_ADDR)
    execute_manager(settings)

if __name__ == '__main__':
    sys.exit(main())
