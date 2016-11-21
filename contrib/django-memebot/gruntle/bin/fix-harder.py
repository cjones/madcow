#!/usr/bin/env python

import urlparse
import sys
import os
import re

import logging as log
log.basicConfig(level=log.ERROR, stream=sys.stderr)

from django.core.management import setup_environ
import settings

setup_environ(settings)

from memebot.models import Link, Source
from memebot.utils.browser import Browser
from memebot.scanner import get_scanners

browser = Browser(user_agent='firefox', timeout=20, max_read=2097152)
scanners = get_scanners(settings.SCANNERS)


def resolve_url(link):
    """Handler for a single link"""
    # fetch url we are processing
    try:
        response = browser.open(link.url, follow_meta_redirect=True)
    except:
        print 'timeout'
        return
    if not response.is_valid:
        print 'invalid response'
        return

    # run through each configured scanner until something matches
    for scanner_name, scanner in scanners:
        try:
            result = scanner.scan(response, log, browser)
            break
        except:
            pass
    else:
        print 'no handler'
        return

    log.info('MATCH on %s: %r', scanner_name, result)

    return scanner_name, result

    '''
    # store rendered results from scanners to link and publish (deferred)

    # XXX some seriously broken shit going on witih emoji combinatorials, hack to make the links flow again
    #link.title = result.title

    '''

def main():
    from django.db.models import Q
    badchar = '>'
    bad_url = Q(url__contains=badchar)
    bad_norm = Q(normalized__contains=badchar)
    bad_res = Q(resolved_url__contains=badchar)
    bad_fields = Q(bad_url | bad_norm | bad_res)
    links = Link.objects.all()
    bad_links = links.filter(bad_fields)
    nbad_link = bad_links.count()
    fix_count = 0
    skip_count = 0
    try:
        for bad_link in bad_links.distinct().order_by('id'):
            found = False
            wontfix = False
            dirty = False
            for key in 'url', 'normalized', 'resolved_url':
                url = getattr(bad_link, key, None)
                if url is not None and badchar in url:
                    found = True
                    uri = urlparse.urlparse(url)
                    clean = []
                    for i, field in enumerate(uri):
                        j = field.find(badchar)
                        if j < 0:
                            keep = field
                        else:
                            keep = field[:j]
                        clean.append(keep)
                    clean_url = urlparse.urlunparse(clean)
                    query = {key: clean_url}
                    dupes = Link.objects.filter(**query)
                    ndupe = dupes.count()
                    if ndupe > 0:
                        wontfix = True
                        break
                    setattr(bad_link, key, clean_url)
                    dirty = True
            if not found:
                raise RuntimeError
            if wontfix or not dirty:
                skip_count += 1
            else:
                bad_link.save()
                fix_count += 1
            done = skip_count + fix_count
            sys.stderr.write('{} / {}\r'.format(done, nbad_link))
            sys.stderr.flush()
    finally:
        print 'skipped: {}'.format(skip_count)
        print 'fixed: {}'.format(fix_count)

    return 0

if __name__ == '__main__':
    sys.exit(main())
