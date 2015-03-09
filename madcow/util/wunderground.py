#!/usr/bin/env python

"""Front-end for talking to Weather Underground RESTful API, geared for IRC"""

from collections import MutableMapping, Mapping, Iterator, Iterable
from functools import partial
from urlparse import ParseResult, urlunparse
from urllib2 import build_opener, Request, HTTPCookieProcessor
from cookielib import CookieJar
from gzip import GzipFile

import traceback
import select
import json
import sys
import abc
import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


__version__ = '0.1'
__license__ = 'BSD (simplified, 2-clause)'
__author__ = 'Chris Jones <cjones@gmail.com>'
__all__ = ['WeatherUnderground', 'APILookupError']


class APILookupError(RuntimeError):
    """Generic error during API request or parsing"""


class URI(ParseResult):
    """Universal Resource Identifier"""

    def __new__(cls, scheme='http', netloc='localhost', path='/', query='', params='', fragment=''):
        return super(URI, cls).__new__(cls, scheme, netloc, path, query, params, fragment)

    def to_url(self):
        return urlunparse(self)

    url = property(to_url)


class ErrorTrapper(object):
    """Context manager to swallow exceptions. Traps the types given in init"""

    def __init__(self, *exc_types):
        self.exc_types = exc_types

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *args, **kwargs):
        return self.is_trappable(exc_type)

    def is_trappable(self, exc_type):
        if exc_type is None:
            return True
        return exc_type in self.exc_types


class PermissiveErrorTrapper(ErrorTrapper):
    """Like ErrorTrapper, but trap everything *except* the provided types"""

    def is_trappable(self, exc_type):
        return not super(PermissiveErrorTrapper, self).is_trappable(exc_type)


class DebugPermissiveErrorTrapper(PermissiveErrorTrapper):
    """
    use to dump exceptions to stderr while developing.
    replace trapall with an instance of this 
    """

    def __init__(self, *exc_types, **opts):
        file = opts.pop('file', None)
        if file is None:
            file = sys.stderr
        if opts:
            raise TypeError('unknown keywords to init', opts)
        self.file = file
        super(DebugPermissiveErrorTrapper, self).__init__(*exc_types)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        trappable = self.is_trappable(exc_type)
        if trappable and exc_type is not None:
            self.file.write('*** TRAPPED EXCEPTION ***\n')
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=self.file)
        return trappable


trapall = PermissiveErrorTrapper(SystemExit, KeyboardInterrupt)
trapio = ErrorTrapper(IOError, OSError, select.error)
trapstd = ErrorTrapper(StandardError)
#trapall = DebugPermissiveErrorTrapper(SystemExit, KeyboardInterrupt)


class ContainerType(abc.ABCMeta):
    """meta-class wankery: magically wrap underlying dict"""

    def __new__(typ, name, bases, attrs):
        for key in map('__{}__'.format, 'getitem setitem delitem iter len str repr'.split()):
            attrs[key] = (lambda k: lambda s, *x, **y: getattr(s.__dict__, k)(*x, **y))(key)
        return super(ContainerType, typ).__new__(typ, name, bases, attrs)


class Container(MutableMapping):
    """Container type that allows both dictionary and attribute access"""

    __metaclass__ = ContainerType

    def __init__(self, *args, **opts):
        self.__dict__ = dict(*args, **opts)

    @classmethod
    def wrap(cls, obj):
        """recursively walk arbitary data structure, replacing dictionaries with Container"""
        t = type(obj)
        s = lambda *x: issubclass(t, x)
        if s(Mapping):
            if not s(cls):
                obj = cls(obj)
            for key, val in obj.iteritems():
                obj[cls.wrap(key)] = cls.wrap(val)
        elif s(Iterator, Iterable) and not s(basestring):
            obj = map(cls.wrap, obj)
        return obj


class Agent(object):
    """Used to make HTTP requests, handles gzip compression"""

    def __init__(self, agent=None, log=None):
        if agent is None:
            agent = ' '.join(['Mozilla/5.0 (compatible; Windows NT 6.1)', 'MSIE/7.0'])
        self.log = log
        self.agent = agent
        self.jar = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.jar))
        del self.opener.addheaders[:]

    def open(self, url, data=None, timeout=None, referer=None):
        """Fetch the url, returning a fileobj. Handles gzip encoded responses"""
        if isinstance(url, URI):
            url = url.to_url()
        if self.log is not None:
            self.log.info('API REQ: {!r}'.format(url))
        req = Request(url, data=data)
        req.add_header('Cache-Control', 'max-age=0')
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
        if self.agent:
            req.add_header('User-Agent', self.agent)
        req.add_header('DNT', '1')
        req.add_header('Accept-Encoding', 'gzip')
        req.add_header('Accept-Language', 'en-US,en;q=0.8')
        if referer:
            req.add_header('Referer', referer)
        res = self.opener.open(req, timeout=timeout)
        reader = res
        info = res.info()
        enc = info.getheader('content-encoding')
        if enc == 'gzip':
            reader = GzipFile(fileobj=StringIO(reader.read()), mode='r')
        return reader


class WeatherUnderground(object):
    """Python interface to Weather Underground API"""

    # regex used for inline temperature colorizer
    _tcol1_re = re.compile(ur'([^0-9])([23456789]0)({}?s)'.format(re.escape(u"'")), re.I | re.U)
    _tcol2_re = r2 = re.compile(ur'(around\s+)(\d+)()([^0-9])', re.I | re.U)

    # format string for get_storm_data method
    _storm_fmt = (u'{stormInfo.stormName_Nice} ({stormInfo.stormNumber}, '
                  u'cat {Current.SaffirSimpsonCategory}) '
                  u'@{Current.lat},{Current.lon}: Winds {wind} | Gusting {gust}')

    # unicode degree symbol
    _deg = u'\u02da'

    def __init__(self, api_key, lang='EN', prefer_metric=False,
                 primary_only=False, api_scheme='http', fsep=' | ',
                 api_netloc='api.wunderground.com',
                 user_agent=None, timeout=10, log=None):
        """
        api_key - (str) REQUIRED! Sign up at api.wunderground.com for one.

        lang - (str) [default: EN] The language localization to use. See API
               docs for possible values.

        prefer_metric - (bool) Prefer metric over imperial values. See the
                        docstring for the conv() method for a more in-depth
                        explanation of this setting and the next.

        primary_only - (bool) Only show one value (based on the prefer_metric
                       setting) rather than display the other in paranthesis
                       after. e.g., display "70 F" instead of "70 F (21 C)".
                       See also the docstring for the conv() method.

        api_scheme - (str) [default: "http"] Protocol for api request.

        fsep - (str) [default: " | "] Used to separate multiple data
               fields in the response.

        api_netloc - (str) [default: "api.wunderground.com"] Hostname to make
                     API requests to.

        agent - (str) User agent to use in request headers. Defaults to
                impersonate a browser in a generic way, mostly for consistency
                with other madcow modules that rely more heavily on scraping
                rather than API access. If you want to be a good netizen or
                some nonsense, you can change this to announce you'r a bot.

        timeout - [default: 10 seconds] Timeout for HTTP requests, may be an
                  integer, float, or None to wait forever. You probably don't
                  want to do that, since it would tie up the bot's workers.
                  NOTE: setting this to 0 makes polling non-blocking, and
                  will cause timeout errors if at any point there's no data
                  to read yet.

        log - A logger object (that is, having info/warn/error/debug methods).
              This will normally inherit madcow's logger, but you can pass
              a generic logging.Logger instance if using standalone. Passing
              None will disable logging.
        """
        self.api_key = api_key
        self.lang = lang
        self.prefer_metric = prefer_metric
        self.primary_only = primary_only
        self.api_scheme = api_scheme
        self.fsep = fsep
        self.api_netloc = api_netloc
        self.agent = Agent(user_agent, log=log)
        self.timeout = timeout
        self.log = log

    ### LOW-LEVEL API ACCESS AND FORMATTERS / HELPERS ###

    def lookup(self, loc=None, features=None, pws=False, best=False):
        """
        The low-level handler to generate api queries, returning the parsed
        result.

        loc -  Location to query. See wunderground api docs for the various
               formats it accepts. Very little pre-processing is done. It will
               separate comma-separated fields into a path, like so:
               "California, CA" becomes "/CA/California", but otherwise it
               uses this field as is. Pass a list of path parts or the
               already-constructed path for finer control.

        features -  Which features to make in the request. See API docs for
                    available features. This depends also on your access
                    level. Mostly you will only use "conditions", which is
                    the default if nothing is provided.

        pws - (bool) Whether to query personal weather stations or not. When
              false, it will use official (airports, etc.) sources only. If
              you live far away from the station, this may be not-so-accurate,
              and you can usually find a closer "personal weather station".
              PWS are run by amateurs, and anyone can do so and submit data to
              WU, so their accuracy is sometimes poor due to improper setup
              (left in the sun, broken/miscalibrated equipment, and so on).
              You can also specify the PWS station ID directon in the loc
              field to choose one in particular.

        best - (bool) I literally have no idea what this does and can't be
               bothered to find out. Try it! It sets "bestfct:1" in the api
               request. Since it's off by default, I bet "best" is a
               misleading way to think of whatever it does.
        """
        if loc is None:
            loc = []
        else:
            if isinstance(loc, (int, long)):
                loc = str(loc)
            if isinstance(loc, basestring):
                loc = [loc]
            else:
                loc = list(loc)
        if not loc:
            loc.append('autoip')
        if len(loc) == 1 and ',' in loc[0]:
            loc[:] = reversed(re.split('\s*,\s*', loc[0]))
        if features is None:
            features = []
        elif isinstance(features, basestring):
            features = [features]
        else:
            features = list(features)
        if not features:
            features.append('conditions')
        path = ['', 'api', self.api_key]
        path.extend(features)
        path.append('lang:' + self.lang)
        path.append('pws:' + str(int(pws)))
        path.append('bestfct:' + str(int(best)))
        path.append('q')
        path.extend(loc)
        uri = URI(self.api_scheme, self.api_netloc, '/'.join(path) + '.json')
        url = uri.to_url()
        res = self.agent.open(url, timeout=self.timeout)
        data = json.load(res)
        response = data.pop('response')
        error = response.pop('error', None)
        if error:
            raise APILookupError(error)
        return Container.wrap(data)

    def convert(self, data, name, metric, usa, prec=1, sep='_', pad=' ', prefer_metric=None, primary_only=None):
        """
        This method is called to sort out whether to return metric or imperial
        for data fields which have both. It takes the response dictionary and
        folds the 2 fields into a single answer, making it easier to simply
        use the dictionary to fill a static format string, instead of worrying
        about whether to use, for example, the "temp_f" or "temp_c" fields. It
        will be in "temp" after this method returns.

        primary_only  (bool) If set to a non-None value, will override the
                      instance default. When this is set, only return one of
                      the 2 values (metric or imperial) and discard the other.
                      Which is chosen depends on the "prefer_metric" setting.

        prefer_metric (bool) If set to a non-None value, will override the
                      instance default. When primary_only is True, this
                      controls which units are kept. When primary_only is
                      false, both are returned, but with one in paranthesis.
                      This controsl which should be shown first.

        data          (dict) The response dict to modify. It needs to contain
                      2 fields that have the same prefix, one for metric and
                      one for imperial. For example, wind_kph and wind_mph.

        name          (str) This is the prefix part of the string, such as
                      "wind" for wind_kph.

        metric        (str) The metric unit (e.g. "kph", "cm", "c").

        usa           (str) The imperial unit (e.g. "mi", "in", "f").

        prec          (int) How many decimal places of precision to retain.
                      Note that integers will gain zero-padding to have a
                      consistent length, so specify 0 if you only have
                      integers.

        sep           (str) [default: "_"] The string that separates the name
                      from its unit. This exists for the few oddball fields
                      that aren't separated by an underscore.

        pad           (str) [default: " "] Padding to use between the number
                      and the unit in the formatted output.
        """
        if prefer_metric is None:
            prefer_metric = self.prefer_metric
        if primary_only is None:
            primary_only = self.primary_only
        if prec == 0:
            fmt = '{}'.format
        else:
            fmt = '{{:.{}f}}'.format(prec).format
        res = []
        for unit in metric, usa:
            key = name + sep + unit
            val = data[key]
            if isinstance(val, basestring):
                val = float(val)
            val = fmt(round(val, prec)) + pad + unit
            res.append(val)
        metric, usa = res
        if prefer_metric:
            pri, sec = metric, usa
        else:
            pri, sec = usa, metric
        if primary_only:
            return pri
        else:
            return u'{} ({})'.format(pri, sec)

    def format_temp(self, fval, prefer_metric=None, primary_only=None):
        """
        Given a temperature in fahranheit, return a formatted string. This
        includes colorizing it (if enabled), converting to Celcius if metric
        is the preferred unit format (which can be overridden by passing a
        bool to either prefer_metric or primary_only)
        """
        if prefer_metric is None:
            prefer_metric = self.prefer_metric
        if primary_only is None:
            primary_only = self.primary_only
        fval = float(fval)
        cval = round((fval - 32.0) * (5.0 / 9.0), 1)
        c0 = c1 = ''
        f, c = map(u'{}{:.1f} {}{}{}'.format, (c1, c1), (fval, cval), (self._deg, self._deg), 'FC', (c0, c0))
        if prefer_metric:
            pri, sec = c, f
        else:
            pri, sec = f, c
        if primary_only:
            return pri
        return u'{} ({})'.format(pri, sec)

    def lookup_current(self, loc, data=None, pws=False, best=False):
        if data is None:
            data = self.lookup(loc, features=['conditions'], pws=pws, best=best)
        cur = data.get('current_observation')
        if cur is None:
            raise APILookupError("invalid api response, this shouldn't happen.")
        return data, cur

    ### HUMAN-READABLE LOOKUP METHODS ###

    def get_basic_conditions(self, loc, data=None, pws=False, best=False, **opts):
        """
        The most basic/slim lookup only returns the temperature, short summary
        of conditions, and location. Best as a default option, as it is less
        spammy than the rest.
        """
        data, cur = self.lookup_current(loc, data, pws, best)
        pods = []
        with trapall:
            pods.append(cur.weather)
        with trapall:
            pods.append(self.format_temp(cur.temp_f, **opts))
        res = self.fsep.join(pods)
        if not res:
            raise APILookupError('no suitable response available')
        with trapall:
            res = cur.display_location.full + u': ' + res
        return res

    def get_extended_conditions(self, loc, data=None, pws=False, best=False, **opts):
        """
        Adds some more fields to the response from get_basic_conditions. Medium
        level spamminess, still generally useful data.
        """
        data, cur = self.lookup_current(loc, data, pws, best)
        conv = partial(self.convert, cur, **opts)
        pods = []
        with trapall:
            pods.append(self.get_basic_conditions(loc, data=data, pws=pws, best=best, **opts))
        with trapall:
            if float(cur.feelslike_f) != float(cur.temp_f):
                cur.feels = self.format_temp(cur.feelslike_f, **opts)
                pods.append(u'Feels Like: ' + cur.feels)
        with trapall:
            pods.append(u'Humidity: ' + cur.relative_humidity)
        with trapall:
            if cur.wind_mph or cur.wind_kph:
                cur.wind = conv('wind', metric='kph', usa='mph')
                pods.append(u'Wind: ' + cur.wind)
                with trapall:
                    pods[-1] += u' {}{} {}'.format(cur.wind_degrees, self._deg, cur.wind_dir)
                if cur.wind_gust_kph or cur.wind_gust_mph:
                    cur.gust = conv('wind', metric='kph', usa='mph')
                    if cur.gust != cur.wind:
                        pods.append(u'Gusting: ' + cur.gust)

        res = self.fsep.join(pods)
        if not res:
            raise APILookupError('no suitable response available')
        return res

    def get_full_conditions(self, loc, data=None, pws=False, best=False, **opts):
        """
        This is get_extended_conditions with the kitchen sink thrown in.
        Arguably of dubious value to anyone but a meterologist, who almost
        certainly use noaa insteead of wunderground, so I don't know why this
        exists, but here it is for completeness.

        (Some fields not present because they were not filled in
        properly/consistently when I tested them, or just returned "N/A" or
        None, or sometimes didn't exist in the response.
        """
        data, cur = self.lookup_current(loc, data, pws, best)
        pods = []
        with trapall:
            pods.append(self.get_extended_conditions(loc, data=data, pws=pws, best=best, **opts))
        conv = partial(self.convert, cur, **opts)
        with trapall:
            cur.visibility= conv('visibility', metric='km', usa='mi')
            pods.append(u'Visibility: ' + cur.visibility)
        with trapall:
            cur.pressure = conv('pressure', metric='mb', usa='in')
            pods.append(u'Pressure: ' + cur.pressure)
        with trapall:
            cur.dewpoint = self.format_temp(cur.dewpoint_f, **opts)
            pods.append(u'Dew Point: ' + cur.dewpoint)
        with trapall:
            obvs = []
            with trapall:
                obvs.append(u'at ' + cur.station_id)
            with trapall:
                obvs.append(u'in ' + cur.observation_location.full)
            obvs = u' '.join(obvs)
            if obvs:
                pods.append(u'Observed ' + obvs)
        with trapall:
            pods.append(cur.observation_time)
        res = self.fsep.join(pods)
        if not res:
            raise APILookupError('no suitable response available')
        return res

    def get_almanac_data(self, loc, data=None, pws=False, best=False, **opts):
        """
        Alternate data query: Gets historic record/typical low/high
        temperatures for the given location on this day. This data may not be
        available for every area as widely as current weather data is, and
        will return an error if it cannot return a useful response.
        """
        if data is None:
            data = self.lookup(loc, features=['almanac', 'conditions'], pws=pws, best=best)
        almanac = data.get('almanac')
        if almanac is None:
            raise APILookupError("no almanac data in response")
        pods = []
        for info, name in [(almanac.temp_low, u'Low'), (almanac.temp_high, u'High')]:
            with trapall:
                pods.append(u'Record {}: {}'.format(name, self.format_temp(info.record.F, **opts)))
                if info.recordyear:
                    pods[-1] += u' in {}'.format(info.recordyear)
            with trapall:
                pods.append(u'Normal {}: {}'.format(name, self.format_temp(info.normal.F, **opts)))
        if not pods:
            raise APILookupError('no valid almanac data available to satisfy request')
        with trapall:
            pods.append(u'Current: ' + self.format_temp(data.current_observation.temp_f, **opts))
        res = self.fsep.join(pods)
        if not res:
            raise APILookupError('empty response building almanac response')
        with trapall:
            res = data.current_observation.display_location.full + u': ' + res
        return res

    def get_forecast_data(self, loc, data=None, pws=False, best=False, num=4, **opts):
        """
        Alternate data query: Get the human-readable forecast for the next
        week. By default it trims the response to 3 "periods" (day and night
        are a period each) to limit spam.
        """
        if data is None:
            data = self.lookup(loc, features=['forecast', 'conditions'], pws=pws, best=best)
        out = []
        with trapall:
            out += [u'* {}: {}'.format(f.title, f.fcttext) for f in data.forecast.txt_forecast.forecastday[:num]]
        res = u'\n'.join(out)
        if not res:
            raise APILookupError('unable to fetch extended forecast data')
        with trapall:
            return u'Extended forecast for {}:\n{}'.format(data.current_observation.display_location.full, res)

    def get_storm_data(self, loc, data=None, pws=False, best=False, **opts):
        """
        Alternate data query: Get tracked storm/hurricane conditions. It is
        unclear whether it matters what is in the loc field.
        """
        if data is None:
            data = self.lookup(loc, features=['currenthurricane'], pws=pws, best=best)
        storms = data.get('currenthurricane')
        if not storms:
            raise APILookupError('no storm data found')
        res = u'\n'.join(self._storm_fmt.format(
            wind=self.convert(storm.Current.WindSpeed, '', metric='Kph', usa='Mph', sep='', **opts),
            gust=self.convert(storm.Current.WindGust, '', metric='Kph', usa='Mph', sep='', **opts),
            **storm) for storm in storms)
        if not res:
            raise APILookupError('no parseable storm data found')
        return u'Currently tracked storms or hurricanes:\n' + res


def main(argv=None):
    """command-line interface"""
    k = 'XXX'
    q = 94005
    w = WeatherUnderground(k)
    print w.get_basic_conditions(q)
    print w.get_extended_conditions(q)
    print w.get_full_conditions(q)
    print w.get_almanac_data(q)
    print w.get_forecast_data(q)
    print w.get_storm_data(q)
    return 0

if __name__ == '__main__':
    sys.exit(main())
