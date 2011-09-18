#!/usr/bin/python

import sys
from django.core.management import execute_manager

sys.dont_write_bytecode = True

import settings

def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'runserver':
        server_addr = getattr(settings, 'DEV_SERVER_ADDR', None)
        if server_addr:
            sys.argv.append(server_addr)
    execute_manager(settings)

if __name__ == '__main__':
    sys.exit(main())
