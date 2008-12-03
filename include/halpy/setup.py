#!/usr/bin/env python

import sys
from distutils.core import setup

if __name__ == '__main__':
    try:
        version = __import__('hal').__version__
    except ImportError, error:
        print >> sys.stderr, 'missing dependency: %s' % error
        sys.exit(1)

    setup(name='hal',
          version=version,
          py_modules=['hal'],
          scripts=['hal.py'],
          description='Heuristically programmed ALgorithmic Computer',
          author='Chris Jones',
          author_email='cjones@gruntle.org',
          url='http://gruntle.org/projects/hal/')

    sys.exit(0)
