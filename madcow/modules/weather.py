"""Get weather report"""

from madcow.util import Module, encoding
from madcow.util.http import geturl
from madcow.util.text import *
from urlparse import urljoin
from learn import Main as Learn
from madcow.util.color import ColorLib
from xml.etree import ElementTree
import re

USAGE = u'set location <nick> <location>'

class Weather(object):

    base_url = u'http://api.wunderground.com/'
    locate_url = urljoin(base_url, u'auto/wui/geo/GeoLookupXML/index.xml')
    station_url = urljoin(base_url, u'auto/wui/geo/WXCurrentObXML/index.xml')
    pws_url = urljoin(base_url, u'weatherstation/WXCurrentObXML.asp')
    forecast_url = urljoin(base_url, u'auto/wui/geo/ForecastXML/index.xml')

    def __init__(self, colorlib, logger):
        self.colorlib = colorlib
        self.log = logger

    def _color_temp(self, temp, tempstr):
        '''colorize the temperature string (tempstr) based on the temperature in farenheit (temp)'''
        blink = False
        if temp < 0:
            color = u'magenta'
        elif temp >=0 and temp < 40:
            color = u'blue'
        elif temp >= 40 and temp < 60:
            color = u'cyan'
        elif temp >= 60 and temp < 80:
            color = u'green'
        elif temp >= 80 and temp < 90:
            color = u'yellow'
        elif temp >= 90 and temp < 100:
            color = u'red'
        elif temp >= 100:
            color = u'red'
            blink = True
        s = self.colorlib.get_color(color, text=tempstr)

        # XXX this seems ill-conceived
        if blink:
            s = u'\x1b[5m' + s + u'\x1b[0m'
        
        return s
    
    def _format_weather(self, data):
        data['tempstr'] = self._color_temp(data['temp'], data['tempstr'])

        return ('%(loc)s - %(time)s: Conditions: %(conditions)s | Temperature: %(tempstr)s ' + \
                '| Humidity: %(humidity)s | Wind: %(wind)s') % data

    def forecast(self, location):
        '''get weather forecast'''
        try:
            page = geturl(url=self.forecast_url, opts={u'query':location})
            xml = ElementTree.fromstring(page)
            text = xml.find('.//fcttext').text
        except Exception, e:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(e)
            return "error looking up forecast for location: %s" % location

        return text

    def official_station(self, location):
        '''gets weather data from an official station (typically an airport)'''
        try:
            page = geturl(url=self.station_url, opts={u'query':location})
            xml = ElementTree.fromstring(page)

            loc = xml.find('display_location/full').text
            time = xml.find('local_time').text
            conditions = xml.find('weather').text
            temp = float(xml.find('temp_f').text)
            tempstr = xml.find('temperature_string').text
            humidity = xml.find('relative_humidity').text
            wind = xml.find('wind_string').text

            return self._format_weather(locals())
        except Exception, e:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(e)
            return "error looking up conditions for location: %s" % location


    def personal_station(self, location):
        '''gets weather data from a personal weather station'''
        try:
            if re.match('[A-Z]{8}\d+', location): # already a PWSid
                pws_id = location
            else:
                page = geturl(url=self.locate_url, opts={u'query':location},
                              referer=self.base_url)
                
                page = page.encode('ascii', 'replace') # ElementTree no likey unicode
                                
                xml = ElementTree.fromstring(page)
                pws_id = xml.find('.//pws/station[1]/id').text
            
            page = geturl(url=self.pws_url, opts={u'ID':pws_id})
            page = page.encode('ascii', 'replace') # ElementTree no likey unicode

            xml = ElementTree.fromstring(page)

            loc = xml.find('location/full').text
            time = xml.find('observation_time_rfc822').text
            conditions = 'N/A'
            temp = float(xml.find('temp_f').text)
            tempstr = xml.find('temperature_string').text
            humidity = xml.find('relative_humidity').text + '%'
            wind = xml.find('wind_string').text

            return self._format_weather(locals())
        except Exception, e:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(e)
            return "error looking up conditions for location: %s" % location



class Main(Module):

    pattern = re.compile(u'^\s*(fc|forecast|weather|ws|pws)(?:\s+(.*)$)?')
    require_addressing = True
    help = u'fc|forecast, ws|weather, pws [zipcode|city,state|city,country|pws] - look up weather forecast/conditions'
    error = u"Couldn't find that place, maybe a bomb dropped on it"

    def init(self):
        colorlib = self.madcow.colorlib
        self.weather = Weather(colorlib, self.log)
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
            if cmd in ('fc', 'forecast'):
                message = self.weather.forecast(location)
            elif cmd in ('weather', 'ws'):
                message = self.weather.official_station(location)
            elif cmd == 'pws':
                message = self.weather.personal_station(location)
        else:
            message = u"I couldn't look that up"
        return u'%s: %s' % (nick, message)


whitespace = re.compile(r'\s+')
year = re.compile(r'\(\d{4}\)\s*$')
badchars = re.compile(r'[^a-z0-9 ]', re.I)

