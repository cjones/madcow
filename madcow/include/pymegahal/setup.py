#!/usr/bin/env python

from distutils.core import setup, Extension
import sys
import os

def main():
    """Build megahal lib and copy to dst"""
    setup(name='megahal',
          version='9.0.3',
          author='David N. Welton',
          author_email='david@dedasys.com',
          url='http://www.megahal.net',
          license='GPL',
          description='markov bot',
          ext_modules=[Extension('cmegahal', ['python.c', 'megahal.c'])])
    return 0

if __name__ == '__main__':
    sys.exit(main())
