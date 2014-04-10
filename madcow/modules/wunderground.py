"""Query Weather Underground API in various ways"""

from madcow.util.wunderground import WeatherUnderground, APILookupError
from madcow.util import Module
from madcow.conf import settings
from learn import Main as Learn

import re

class Main(Module):

    defaults = {
            'api_key': 'CHANGEME',
            'lang': 'EN',
            'prefer_metric': False,
            'primary_only': False,
            'api_scheme': 'http',
            'api_netloc': 'api.wunderground.com',
            'do_color': True,
            'user_agent': None,
            'timeout': 10,
            }

    trigger_map = {
            'conditions': {
                True: {
                    'basic': ['pwb', 'pw'],
                    'extended': ['pws', 'pwd'],
                    'full': ['pwsx', 'pwdx'],
                    },
                False: {
                    'basic': ['wb'],
                    'extended': ['ws', 'weather', 'weath'],
                    'full': ['wsx'],
                    },
                },
            'data': {
                False: {
                    'almanac': ['alma', 'almanac', 'records', 'highs', 'lows'],
                    'forecast': ['forecast', 'fc', 'fce', 'fcx'],
                    'storm': ['storm', 'storms', 'hurricane', 'hurricanes'],
                    },
                },
            }

    triggers = set()
    _method_triggers = []
    help_lines = [u'Weather Underground query shortcuts:']
    for query_type, station_types in trigger_map.iteritems():
        for pws, handlers in station_types.iteritems():
            for handler, _triggers in handlers.iteritems():
                if _triggers:
                    triggers.update(_triggers)
                    trigger_desc = u'[{}]'.format('|'.join(_triggers))
                    if query_type == 'conditions':
                        meth_desc = u'look up weather conditions'
                        notes = []
                        if pws:
                            notes.append(u'include personal weather stations')
                        else:
                            notes.append(u'official stations only')
                        if handler == 'basic':
                            notes.append(u'brief result')
                        if handler == 'full':
                            notes.append(u'extended result')
                        if notes:
                            meth_desc += u' ({})'.format(', '.join(notes))
                    else:
                        meth_desc = u'look up extended {} data'.format(handler)
                    triggers.update(_triggers)
                    help_lines.append(u'{} - {}'.format(trigger_desc, meth_desc))
                    _method_triggers.append(('get_{}_{}'.format(handler, query_type), frozenset(_triggers), pws))

    help = u'\n'.join(help_lines)
    regex = r'^\s*({})(?:\s+(.+?))?\s*$'.format('|'.join(map(re.escape, sorted(triggers))))
    pattern = re.compile(regex, re.IGNORECASE)
    require_addressing = True

    def init(self):
        opts = {}
        for key, default in self.defaults.iteritems():
            setting = 'WUNDERGROUND_' + key.upper()
            val = getattr(settings, setting, None)
            if val is None:
                val = default
            opts[key] = val

        self.api = WeatherUnderground(log=self.madcow.log, **opts)
        self.learn = Learn(madcow=self.madcow)
        self.method_triggers = [(getattr(self.api, method_name), triggers, pws)
                                for method_name, triggers, pws in self._method_triggers]

    def response(self, nick, args, kwargs, _strip=lambda x: x.strip()):
        trigger, query = ('' if arg is None else _strip(arg) for arg in args)
        trigger = trigger.lower()
        for method, triggers, pws in self.method_triggers:
            if trigger in triggers:
                res = None
                break
        else:
            res = u': internal configuration error: no handler found for that keyword.'
        if not res:
            if not query:
                loc = self.learn.lookup('location', nick)
            elif query.startswith(u'@'):
                loc = self.learn.lookup('location', query[1:])
            else:
                loc = query
            if loc:
                try:
                    res = method(loc, pws=pws)
                except APILookupError, exc:
                    res = u'API lookup error: {}'.format(exc.message)
            else:
                res = u"I couldn't look that up: be sure to specify a query or set your default location with: set location <nick> <zip|city|airport_code>"
        if len(_strip(res).splitlines()) == 1:
            res = u'{}: {}'.format(nick, res)
        return res
