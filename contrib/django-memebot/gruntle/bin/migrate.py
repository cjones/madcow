#!/usr/bin/env python

from os.path import *
import sys
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'gruntle.settings'
prefix = dirname(abspath(__file__))
base = dirname(prefix)
for dir in prefix, base:
    while dir in sys.path:
        sys.path.remove(dir)
    sys.path.insert(0, dir)
sys.dont_write_bytecode = True

from django.conf import settings
from gruntle.memebot import models
from django.db.models import get_models
from django.db.models.fields import AutoField

def main():
    for model in get_models():
        olds = model.objects.using('old').all()
        news = model.objects.using('default').all()
        if olds.count() != news.count():
            print model._meta, olds.count(), news.count()
            for new in news:
                new.delete()

            #if news.count() > 0: print 'problems:', model._meta
            if olds.count() == 0:
                print 'empty:', model._meta
            else:
                for old in olds:
                    attrs = {}
                    for field, _ in model._meta.get_fields_with_model():
                        key = field.attname
                        attrs[key] = getattr(old, key)
                    new = model.objects.using('default').create(**attrs)




    return 0

if __name__ == '__main__':
    sys.exit(main())
