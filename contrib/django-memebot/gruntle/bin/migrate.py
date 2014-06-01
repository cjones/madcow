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
from django.db.models.fields import AutoField, DateTimeField

def main():
    for model in get_models():
        olds = model.objects.using('old').all()
        news = model.objects.using('default').all()
        if olds.count() != news.count():
            print model._meta, olds.count(), news.count()
            for new in news:
                new.delete()
            if olds.count() == 0:
                print 'empty:', model._meta
            else:
                fields = zip(*model._meta.get_fields_with_model())[0]
                keys = []
                for field in fields:
                    if isinstance(field, DateTimeField):
                        field.auto_now_add = field.auto_now = False
                    keys.append(field.attname)
                for old in olds:
                    model.objects.using('default').create(**{key: getattr(old, key) for key in keys})



    return 0

if __name__ == '__main__':
    sys.exit(main())
