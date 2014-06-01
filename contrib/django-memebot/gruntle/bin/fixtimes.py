#!/usr/bin/env python

from itertools import *
from operator import *
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
        fields, models = izip(*model._meta.get_fields_with_model())
        fixes = set()
        for field in fields:
            for key in 'auto_now', 'auto_now_add':
                if getattr(field, key, False):
                    setattr(field, key, True)
                    fixes.add(field.attname)

        if fixes:
            news = model.objects.using('default').all()
            olds = model.objects.using('old').all()
            pk = model._meta.pk.attname
            pkget = attrgetter(pk)
            newpks = imap(pkget, news)
            oldpks = imap(pkget, olds)
            shared = set(oldpks) & set(newpks)
            olds = olds.filter(pk__in=shared)
            news = news.filter(pk__in=shared)
            lookupnew = {new.pk: new for new in news}
            for old in olds:
                new = lookupnew[old.pk]
                updates = {attr: getattr(old, attr) for attr in fixes}
                model.objects.filter(pk=new.pk).update(**updates)

    return 0

if __name__ == '__main__':
    sys.exit(main())
