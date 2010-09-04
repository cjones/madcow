#!/usr/bin/env python

from distutils.core import setup, Extension
import shutil

# hack to maybe work with cygwin
import sys
args = ['build', '--build-lib', 'build']
if '--mingw32' in sys.argv:
    args += ['-c', 'mingw32']

def install():
    setup(name='megahal',
          version='9.0.3',
          author='David N. Welton',
          author_email='david@dedasys.com',
          url='http://www.megahal.net',
          license='GPL',
          description='markov bot',
          script_args = args,
          ext_modules=[Extension('megahal', ['python.c', 'megahal.c'])])
    shutil.copy('build/megahal.so', '../megahal.so')
    shutil.rmtree('build')
    print
    print 'MegaHAL installed!'

if __name__ == '__main__':
    install()
