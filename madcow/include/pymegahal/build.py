from distutils.core import setup, Extension
import shutil
from tempfile import mkdtemp
import os

def build(dst):
    """Build megahal lib and copy to dst"""
    build_dir = mkdtemp()
    try:
        setup(name='megahal',
              version='9.0.3',
              author='David N. Welton',
              author_email='david@dedasys.com',
              url='http://www.megahal.net',
              license='GPL',
              description='markov bot',
              script_args=['build', '--build-lib', build_dir, '--build-base', build_dir],
              ext_modules=[Extension('megahal', ['python.c', 'megahal.c'])])
        shutil.copy(os.path.join(build_dir, 'megahal.so'), dst)
    finally:
        if os.path.exists(build_dir):
            os.removedirs(build_dir)
