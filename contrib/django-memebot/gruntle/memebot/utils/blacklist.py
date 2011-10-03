"""DNS Blacklist"""

import collections
import urlparse
import socket
import re
from django.conf import settings
from gruntle.memebot.decorators import memoize
from gruntle.memebot.utils import text, flatten
from gruntle.memebot.exceptions import BlackListError

__all__ = ['BlackListResult', 'get_blacklist_for_url', 'get_blacklist', 'get_all_hosts', 'check', 'normalize']

BlackListResult = collections.namedtuple('BlackListResult', ('host', 'match', 'rule'))

class DNSBlackList(object):

    """DNS-based blacklist handler"""

    def __init__(self, *rules):
        self.rules = rules
        self._rules_re = None

    def __eq__(self, other):
        if not isinstance(other, DNSBlackList):
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        equals = self.__eq__(other)
        if equals is NotImplemented:
            return equals
        return not equals

    def __hash__(self):
        return hash(self.rules)

    @property
    def rules_re(self):
        """Regular expressions for our blacklist"""
        if self._rules_re is None:
            self._rules_re = dict((rule, self.compile(rule)) for rule in self.rules)
        return self._rules_re

    @memoize
    def compile(self, rule):
        """Compile pattern"""
        return re.compile(r'^%s$' % re.escape(rule).replace('\\*', '.*'))

    @memoize
    def get_all_hosts(self, host):
        """Find all names/aliases/addresses for host"""
        hosts = set()
        checked = set()
        hosts.add(self.normalize(host))

        while True:
            unchecked = hosts.difference(checked)
            if not unchecked:
                break
            for host in unchecked:
                checked.add(host)
                for lookup in socket.gethostbyaddr, socket.gethostbyname_ex:
                    try:
                        results = lookup(host)
                    except socket.error:
                        continue
                    for host in flatten(results):
                        hosts.add(self.normalize(host))

        return tuple(hosts)

    @memoize
    def get_blacklist(self, host):
        """Return blacklist entry if this host matches"""
        orig_host = self.normalize(host)
        for host in self.get_all_hosts(orig_host):
            for rule, blacklist_re in self.rules_re.iteritems():
                if blacklist_re.search(host) is not None:
                    return BlackListResult(host=orig_host, match=host, rule=rule)

    @memoize
    def normalize(self, host):
        """Clean up hostname"""
        items = text.decode(host).lower().rsplit(u':', 1)[0].split(u'.')
        return text.encode(u'.'.join(item for item in (item.strip() for item in items) if item))

    def check(self, val):
        """Given a URL or hostname, raise BlackListError if in our list of hosts"""
        url = urlparse.urlparse(val)
        if url.scheme and url.netloc:
            host = url.netloc
            url = val
        else:
            host = val
            url = None
        result = self.get_blacklist(self.normalize(host))
        if result is not None:
            raise BlackListError(result, url=url)

    @classmethod
    def export_methods(cls, methods, *args, **kwargs):
        """Create default handler and export methods into global namespace, takes same options as constructor"""
        handler = cls(*args, **kwargs)
        context = globals()
        for key in methods:
            if key not in context:
                val = getattr(handler, key, None)
                if val is not None:
                    context[key] = val


DNSBlackList.export_methods(__all__, *settings.MEMEBOT_BLACKLIST)
