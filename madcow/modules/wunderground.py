"""Get weather report"""

from madcow.util import Module, wunderground
from madcow.conf import settings
from learn import Main as Learn
import re

class Main(Module):

    pattern = re.compile(u'^\s*(xfc|xforecast|xweather|xws|xpws|xpwd|xalmanac|xstorms|xstorm|xw|xpw)(?:\s+(.+?))?\s*$')
    require_addressing = True

    help = u'[xfc|xforecast] forecast [xweather|xws] weather [xpws|xpwd] personal weather stations\n'
    help += u'[xalmanac] historic [xstorms|xstorm] storm info'


    def init(self):
        self.wu = wunderground.WeatherUnderground(
                settings.WUNDERGROUND_API_KEY,
                lang=getattr(settings, 'WUNDERGROUND_LANG', None) or 'EN',
                prefer_metric=getattr(settings, 'WUNDERGROUND_PREFER_METRIC', False),
                primary_only=getattr(settings, 'WUNDERGROUND_PRIMARY_ONLY', False),
                api_scheme=getattr(settings, 'WUNDERGROUND_API_SCHEME', None) or 'http',
                api_netloc=getattr(settings, 'WUNDERGROUND_API_NETLOC', None) or 'api.wunderground.com',
                do_color=getattr(settings, 'WUNDERGROUND_DO_COLOR', True),
                user_agent=getattr(settings, 'WUNDERGROUND_USER_AGENT', None),
                timeout=getattr(settings, 'WUNDERGROUND_TIMEOUT', None),
                log=self.madcow.log,
                )
        self.learn = Learn(madcow=self.madcow)

    def response(self, nick, args, kwargs):
        cmd = args[0]
        query = args[1]

        if not query:
            location = self.learn.lookup('location', nick)
        elif query.startswith('@'):
            location = self.learn.lookup('location', query[1:])
        else:
            location = query
        if location:
            if cmd in ('xfc', 'xforecast'):
                message = self.wu.get_forecast(location)
            elif cmd in ('xweather', 'xws'):
                message = self.wu.ext_conditions(location)
            elif cmd in ('xpws', 'xpwd'):
                message = self.wu.ext_conditions(location, pws=True)
            elif cmd in ('xalmanac',):
                message = self.wu.get_almanac(location)
            elif cmd in ('xstorm', 'xstorms'):
                message = self.wu.get_storms(location)
            elif cmd in ('xw'):
                message = self.wu.basic_conditions(location)
            elif cmd in ('xpw'):
                message = self.wu.basic_conditions(location, pws=True)
        else:
            message = u"I couldn't look that up"
        return u'%s: %s' % (nick, message)
