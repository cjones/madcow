#!/usr/bin/env python

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

bad_re = re.compile(r'[>]$')

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
    #sources = Source.objects.all()
    links = Link.objects.all()
    slack_links = links.filter(source__name='hugs', source__type='slack')
    lookups = {}
    fields = 'url', 'normalized', 'resolved_url'

    def add_link(link):
        for field in fields:
            lookup = lookups.setdefault(field, {})
            val = getattr(link, field)
            lookup.setdefault(val, []).append(link)

    map(add_link, slack_links)

    bad_links = slack_links.filter(url__endswith='>')
    nbad_link = bad_links.count()
    for i, link in enumerate(bad_links):
        print i + 1, '/', nbad_link
        new_url = bad_re.sub('', link.url)
        if new_url == link.url:
            print 'not actually bad for some reason'
        else:
            sibs = lookups['url'].get(new_url)
            if sibs is not None:
                print 'skipping fixup because the fixed url already exists'
            else:
                link.url = new_url
                new_normalized = Link.objects.normalize_url(new_url)
                sibs = lookups['normalized'].get(new_normalized)
                if sibs is None:
                    ok = True
                else:
                    temp = set(sibs)
                    if link in temp:
                        temp.remove(link)
                    if temp:
                        ok = False
                    else:
                        ok = True
                if not ok:
                    print 'skipping because the new normalized link already exists'
                else:
                    attr = None
                    if link.resolved_url is not None:
                        result = resolve_url(link)
                        if result is not None:
                            scanner_name, result = result
                            link.resolved_url = result.resolved_url
                            link.content_type = result.content_type
                            link.content = result.content
                            safe_title = result.title
                            if safe_title is not None:
                                if not isinstance(safe_title, unicode):
                                    if not isinstance(safe_title, str):
                                        safe_title = str(safe_title)
                                    safe_title = safe_title.decode('latin1')
                                safe_title = safe_title.encode('ascii', 'ignore')
                                safe_title = safe_title.decode('ascii')
                                safe_title = safe_title.strip()
                                if not safe_title:
                                    safe_title = None
                            link.title = safe_title
                            link.scanner = scanner_name
                            attr = result.attr
                    link.publish(commit=False)
                    link.save()
                    if attr is not None:
                        for key, val in result.attr.iteritems():
                            link.attr[key] = val
                    add_link(link)
                    print 'fixed', link

    return 0

if __name__ == '__main__':
    sys.exit(main())
