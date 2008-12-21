#!/usr/bin/env python

from distutils.core import setup, Extension

longdesc = """MegaHAL is a conversation simulator that can learn as
you talk to it. This module contains Python bindings for the library."""

setup(name="megahal", version="9.0.3",
      author="David N. Welton", author_email="david@dedasys.com",
      url="http://www.megahal.net", license="GPL",
      description="Python bindings for MegaHAL",
      long_description=longdesc,
      ext_modules=[Extension("megahal", ["python.c", "megahal.c"])])
