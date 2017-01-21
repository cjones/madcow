"""Countup from abomination"""

from madcow.util import Module
import re
import time

INAUG_DATES = [
        (1611162000, 'ANYONE',  1),  # 2021-01-20 12:00:00 EST-0500 (2021-01-20 17:00:00 UTC+0000)
        (1484931600, 'trump',   1),  # 2017-01-20 12:00:00 EST-0500 (2017-01-20 17:00:00 UTC+0000)
        (1358701200, 'obama',   2),  # 2013-01-20 12:00:00 EST-0500 (2013-01-20 17:00:00 UTC+0000)
        (1232470800, 'obama',   1),  # 2009-01-20 12:00:00 EST-0500 (2009-01-20 17:00:00 UTC+0000)
        (1106240400, 'gwb',     2),  # 2005-01-20 12:00:00 EST-0500 (2005-01-20 17:00:00 UTC+0000)
        ( 980010000, 'gwb',     1),  # 2001-01-20 12:00:00 EST-0500 (2001-01-20 17:00:00 UTC+0000)
        ( 853779600, 'clinton', 2),  # 1997-01-20 12:00:00 EST-0500 (1997-01-20 17:00:00 UTC+0000)
        ( 727549200, 'clinton', 1),  # 1993-01-20 12:00:00 EST-0500 (1993-01-20 17:00:00 UTC+0000)
        ( 601318800, 'bush',    1),  # 1989-01-20 12:00:00 EST-0500 (1989-01-20 17:00:00 UTC+0000)
        ( 475088400, 'reagan',  2),  # 1985-01-20 12:00:00 EST-0500 (1985-01-20 17:00:00 UTC+0000)
        ( 348858000, 'reagan',  1),  # 1981-01-20 12:00:00 EST-0500 (1981-01-20 17:00:00 UTC+0000)
        ( 222627600, 'carter',  1),  # 1977-01-20 12:00:00 EST-0500 (1977-01-20 17:00:00 UTC+0000)
        (  96397200, 'ford',    1),  # 1973-01-20 12:00:00 EST-0500 (1973-01-20 17:00:00 UTC+0000)
        ( -29833200, 'nixon',   1),  # 1969-01-20 12:00:00 EST-0500 (1969-01-20 17:00:00 UTC+0000)
        (-156063600, 'johnson', 1),  # 1965-01-20 12:00:00 EST-0500 (1965-01-20 17:00:00 UTC+0000)
        (-282294000, 'kennedy', 1),  # 1961-01-20 12:00:00 EST-0500 (1961-01-20 17:00:00 UTC+0000)
        ]

class Main(Module):
    pattern = re.compile(r'^\s*trump\s*$', re.I)
    anyone_inaug_ts = INAUG_DATES[0][0]
    trump_inaug_ts = INAUG_DATES[1][0]
    help = u'trump - get precise time since the american experiment ended'

    def response(self, nick, args, kwargs):
        kwargs['req'].blockquoted = True
        now = time.time()
        elapsed = now - self.trump_inaug_ts
        remain = self.anyone_inaug_ts - now
        return '\n'.join([
            u'Time since the American Experiment ended: {}'.format(self.human_readable(elapsed)),
            u"Minimum time before it's fixable (maybe): {}".format(self.human_readable(remain)),
            ])

    @classmethod
    def human_readable(cls, t):
        s, u = divmod(int(t * 1000), 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        w, d = divmod(d, 7)
        return ' '.join(['{} {}{}'.format(n, u, '' if n == 1 else 's')
            for n, u in zip((y, w / 4, w % 4, d, h, m, s, u),
                'year month week day hour minute second usec'.split()) if n > 0])
