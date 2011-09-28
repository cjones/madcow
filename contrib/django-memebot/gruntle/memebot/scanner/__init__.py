"""Core handler for scanning Link objects"""

import collections
import traceback
import urlparse
import cgi
import re

from django.conf import settings

from gruntle.memebot.decorators import logged, locked
from gruntle.memebot.utils.browser import Browser
from gruntle.memebot.models import Link
from gruntle.memebot.exceptions import *

class ScanResult(collections.namedtuple('ScanResult', 'response override_url title content_type content attr')):

    """Returned from a scanner on succesful match, contains values with which to update Link"""

    @property
    def resolved_url(self):
        """Returns the real URL from the response object unless explicitly overridden"""
        if self.override_url:
            return self.override_url
        return self.response.real_url


class Scanner(object):

    """Base scanner implements url and query context parsing/matching"""

    rss_template = None
    url_match = None

    def __init__(self):
        url_match = getattr(self, 'url_match', None)
        if url_math is None:
            url_math = {]
        self.patterns = dict((field, self.get_regex(url_match, field)) for field in urlparse.ParseResult._fields)
        self.query_patterns = [tuple(self.get_regex(query, key) for key in ('key', 'val'))
                               for query in url_match.get('queries', [])]

    def get_regex(self, match, name):
        """Get compiled regex from pattern spec"""
        exact = match.get(name, None)
        regex = match.get(name + '_regex', None)
        if exact is None and regex is None:
            pattern = ''
        elif exact is None and regex is not None:
            pattern = regex
        elif exact is not None and regex is None:
            pattern = '^' + re.escape(exact) + '$'
        else:
            raise ConfigError('cannot have by exact match and regex specified')
        flags = 0
        if match.get(name + '_icase', False):
            flags |= re.IGNORECASE
        return re.compile(pattern, flags)

    def scan(self, response, log):
        """
        Takes a response object and checks if there the context matches.

        If it matches, this scanners handle() method is called with the
        reponse as the first argument, and any match groups from regular
        expressions as subsequent arguments in the order they are parsed
        (see urlparse.ParseResult._fields for field order).
        Raises NoMatch if not, otherwise calls handle

        If context does not match, NoMatch is raised
        """
        uri = urlparse.urlparse(response.url)
        results = []
        for field in uri._fields:
            regex = self.patterns[field]
            val = getattr(uri, field, '')
            match = regex.search(val)
            if match is None:
                raise NoMatch(response.url, field, val, regex)
            results.extend(match.groups())

        if self.query_patterns:
            queries = cgi.parse_qsl(uri.query)
            for patterns in self.query_patterns:
                for query in queries:
                    matches = []
                    for regex, val in zip(patterns, query):
                        match = regex.search(val)
                        if match is None:
                            break
                        matches.append(match)
                    if len(matches) == 2:
                        for match in matches:
                            results.extend(match.groups())
                        break

                else:
                    raise NoMatch(response.url, 'query', uri.query, *patterns)

        return self.handle(response, log, *results)

    def handle(self):
        raise NotImplementedError


def get_scanners(names):
    """Import configured scanners"""
    func_name = 'scanner'
    global_context = globals()
    local_context = locals()
    scanners = []
    for name in names:
        mod = __import__(name, global_context, local_context, [func_name])
        scanner = getattr(mod, func_name, None)
        if scanner is not None:
            scanners.append((name, scanner))
    return scanners


@logged('scanner', append=True)
@locked('scanner', 0)
def run(logger, max_links=None, dry_run=False, user_agent=None, timeout=None, max_read=None, max_errors=None):
    """Run pending links through scanner API, updating with rendered content and discarding invalid links"""

    # defaults from settings
    if max_links is None:
        max_links = settings.SCANNER_MAX_LINKS
    if user_agent is None:
        user_agent = settings.SCANNER_USER_AGENT
    if timeout is None:
        timeout = settings.SCANNER_TIMEOUT
    if max_read is None:
        max_read = settings.SCANNER_MAX_READ
    if max_errors is None:
        max_errors = settings.SCANNER_MAX_ERRORS

    # initialize scanners and browser
    scanners = get_scanners(settings.SCANNERS)
    if not scanners:
        raise ConfigError('No scanners configured!')
    browser = Browser(user_agent=user_agent, timeout=timeout)

    # fetch new links to scan
    links = Link.objects.filter(state='new').order_by('created')
    if max_links:
        links = links[:max_links]
    num_links = links.count()
    if not num_links:
        log.info('No new links to scan')
        return

    for i, link in enumerate(links):
        log = logger.get_named_logger('%d/%d' % (i + 1, num_links))
        log.info('Scanning: [%d] %s', link.id, link.url)
        try:
            with TrapErrors():

                # fetch url we are processing
                response = browser.open(link.url, max_read=max_read)
                if not response.is_valid:
                    raise BadResponse(link, response)

                # run through each configured scanner until something matches
                for scanner_name, scanner in scanners:
                    try:
                        result = scanner.scan(response, log)
                        break
                    except (NoMatch, InvalidContent):
                        pass
                else:
                    raise ConfigError('No appropriate handler')

                # store rendered results from scanners to link and publish (deferred)
                link.resolved_url = result.resolved_url
                link.content_type = result.content_type
                link.content = result.content
                link.title = result.title
                link.scanner = scanner_name
                link.publish(commit=False)

                # since this writes back immediately, hold until we know if this is a dry run
                link._attr = result.attr

        except TrapError, exc:

            # to match _attr temp storage above
            link._attr = None

            # store stack trace in content field for the record
            link.content_type = 'text/plain'
            link.content = '\n'.join(traceback.format_exception(*exc.args))

            # look for any specific exceptions we are interested in,
            # otherwise dump generic stacktrace/error
            wrapped_exc = exc.args[1]
            if isinstance(wrapped_exc, BadResponse):
                log.warn('Bad request: %s', wrapped_exc)
                fatal = wrapped_exc.fatal
            else:
                log.error('Unhandled exception during scan', exc_info=exc.args)
                fatal = False

            # increment error count, set link to invalid if its failed too many times
            link.error_count += 1
            limit_reached = max_errors is not None and link.error_count >= max_errors
            if fatal or limit_reached:
                link.state = 'invalid'
                if limit_reached:
                    log.error('Discarding %r, error count reached threshold: %d', link, max_errors)
                else:
                    log.error('Discarding %r, error was fatal', link)

        # save changes to this link.. maybe
        if dry_run:
            log.warn('DRY RUN, not saving to database')
        else:
            link.save()
            if link._attr is not None:
                for key, val in link._attr.iteritems():
                    link.attr[key] = val
