
from subprocess import Popen, PIPE
from functools import partial
from urlparse import ParseResult, urlunparse, urlparse
from urllib2 import build_opener, Request, HTTPCookieProcessor
from cookielib import CookieJar
from gzip import GzipFile
from cStringIO import StringIO
import json
import sys
import os
import re

_temp_scale = [(None, '\x1b[0;5;35;40m'),
               ( -20, '\x1b[0;35;40m'),
               (   0, '\x1b[0;1;35;40m'),
               (  15, '\x1b[0;1;34;40m'),
               (  32, '\x1b[0;36;40m'),
               (  50, '\x1b[0;1;36;40m'),
               (  60, '\x1b[0;32;40m'),
               (  68, '\x1b[0;1;32;40m'),
               (  78, '\x1b[0;33;40m'),
               (  84, '\x1b[0;1;33;40m'),
               (  90, '\x1b[0;1;31;40m'),
               (  97, '\x1b[0;31;40m'),
               ( 105, '\x1b[0;5;31;40m')]

x, y = zip(*_temp_scale)
_temp_scale[:] = zip(x, x[1:] + (None,), y)
_sgr0 = '\x1b[0m'
_deg = u'\u02da'


class URI(ParseResult):

    def __new__(cls, scheme='http', netloc='localhost', path='/', query='', params='', fragment=''):
        return super(URI, cls).__new__(cls, scheme, netloc, path, query, params, fragment)

    def to_url(self):
        return urlunparse(self)

    url = property(to_url)


class Agent(object):

    def __init__(self, agent=None, log=None):
        if agent is None:
            agent = ' '.join(['Mozilla/5.0 (compatible; Windows NT 6.1)', 'MSIE/7.0'])
        self.log = log
        self.agent = agent
        self.jar = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.jar))
        del self.opener.addheaders[:]

    def open(self, url, data=None, timeout=None, referer=None):
        if isinstance(url, URI):
            url = url.to_url()
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

    def __init__(self,
                 api_key,
                 lang='EN',
                 prefer_metric=False,
                 primary_only=False,
                 api_scheme='http',
                 api_netloc='api.wunderground.com',
                 do_color=True,
                 user_agent=None,
                 timeout=None,
                 log=None,
                 ):
        self.api_key = api_key
        self.lang = lang
        self.prefer_metric = prefer_metric
        self.primary_only = primary_only
        self.api_scheme = api_scheme
        self.api_netloc = api_netloc
        self.do_color = do_color
        self.agent = Agent(user_agent, log=log)
        self.timeout = timeout
        self.log = log

    def lookup(self, loc=None, features=None, pws=False, best=False):
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
            raise IOError('server returned an error', error)
        return data

    def get_color(self, val):
        for _min, _max, color in _temp_scale:
            if ((_min is None or val >= _min) and
                    (_max is None or val < _max)):
                return color

    def format_temp(self, fval, prefer_metric=None, primary_only=None):
        if prefer_metric is None:
            prefer_metric = self.prefer_metric
        if primary_only is None:
            primary_only = self.primary_only
        fval = float(fval)
        cval = round((fval - 32.0) * (5.0 / 9.0), 1)
        if self.do_color:
            c1 = self.get_color(fval)
            c0 = _sgr0
        else:
            c0 = c1 = ''
        f, c = map(u'{}{:.1f} {}{}{}'.format, (c1, c1), (fval, cval), (_deg, _deg), 'FC', (c0, c0))
        if prefer_metric:
            pri, sec = c, f
        else:
            pri, sec = f, c
        if primary_only:
            return pri
        return u'{} ({})'.format(pri, sec)

    def basic_conditions(self, loc, data=None, pws=False, best=False, **opts):
        if data is None:
            data = self.lookup(loc, features=['conditions'], pws=pws, best=best)
        cur = data['current_observation']
        cur['temp'] = self.format_temp(cur['temp_f'], **opts)
        return u'{display_location[full]}: {weather} | {temp}'.format(**cur)

    def convert(self, data, name, metric, usa, prec=1, sep='_', pad=' ', prefer_metric=None, primary_only=None):
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

    def ext_conditions(self, loc, data=None, pws=False, best=False, **opts):
        if data is None:
            data = self.lookup(loc, features=['conditions'], pws=pws, best=best)
        cur = data['current_observation']
        conv = partial(self.convert, cur, **opts)
        cur['basic'] = self.basic_conditions(loc, data=data, pws=pws, best=best, **opts)
        cur['temp'] = self.format_temp(cur['temp_f'], **opts)
        cur['feels'] = self.format_temp(cur['feelslike_f'], **opts)
        cur['wind'] = conv('wind', metric='kph', usa='mph')
        cur['gust'] = conv('wind_gust', metric='kph', usa='mph')
        cur['deg'] = _deg
        cur['visibility'] = conv('visibility', metric='km', usa='mi')
        cur['pressure'] = conv('pressure', metric='mb', usa='in')
        cur['dewpoint'] = self.format_temp(cur['dewpoint_f'], **opts)
        return u'{basic} | Feels Like: {feels} | Humidity: {relative_humidity} | Wind: {wind} [Gusting: {gust}] {wind_degrees}{deg} {wind_dir} | Visibility: {visibility} | Pressure: {pressure} | Dew Point: {dewpoint} | Observed at {station_id} in {observation_location[full]} | {observation_time}'.format(**cur)

    def get_almanac(self, loc, data=None, pws=False, best=False, **opts):
        if data is None:
            data = self.lookup(loc, features=['almanac'], pws=pws, best=best)
        cur = data['almanac']
        recs = []
        for name in 'low', 'high':
            key = 'temp_' + name
            tmp = cur[key]
            res = []
            for sub in 'record', 'normal':
                res.append(self.format_temp(tmp[sub]['F'], **opts))
            recs.append(u'normal {name}: {normal} | record {name}: {record} in {year}'.format(
                name=name, normal=res[1], record=res[0], year=tmp['recordyear']))
        return u' | '.join(recs)

    def get_forecast(self, loc, data=None, pws=False, best=False, maxlines=3, **opts):
        if data is None:
            data = self.lookup(loc, features=['forecast'], pws=pws, best=best)
        out = []
        for fc in data['forecast']['txt_forecast']['forecastday'][:maxlines]:
            out.append(fc['title'] + ': ' + fc['fcttext'])
        return u'\n'.join(out)

    def get_storms(self, loc, data=None, pws=False, best=False, **opts):
        if data is None:
            data = self.lookup(loc, features=['currenthurricane'], pws=pws, best=best)
        storms = data['currenthurricane']
        rec = []
        for storm in storms:
            info = storm['stormInfo']
            name = info['stormName_Nice']
            num = info['stormNumber']
            current = storm['Current']
            cat = current['SaffirSimpsonCategory']
            speed = self.convert(current['WindSpeed'], '', metric='Kph', usa='Mph', sep='', **opts)
            gust = self.convert(current['WindGust'], '', metric='Kph', usa='Mph', sep='', **opts)
            lat = current['lat']
            lon = current['lon']
            rec.append(u'{} ({}, cat {}) @{},{}: Winds {} | Gusting {}'.format(
                name, num, cat, lat, lon, speed, gust))
        return u'\n'.join(rec)

