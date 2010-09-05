
# Copyright (C) 2007, 2009 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Template for periodic event"""

import logging as log
import urllib2
from madcow import __version__ as current_version

class Main(object):

    url = 'http://dis.gruntle.org/app/madcow/latest/'
    agent = 'Madcow Updater v' + current_version
    msg_fmt = 'Madcow v%(new_version)s is available, you have v%(current_version)s.  Visit http://madcow.googlecode.com/ to update.\x07'
    priority = 0

    def __init__(self, madcow):
        self.madcow = madcow
        self.enabled = madcow.config.updater.enabled
        self.frequency = madcow.config.updater.updatefreq
        self.output = madcow.config.updater.channel
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-Agent', self.agent)]

    def response(self, *args):
        """This is called by madcow, should return a string or None"""
        try:
            log.info('checking for updates for madcow...')
            new_version = self.opener.open(self.url).read().strip()
            if numeric(new_version) > numeric(current_version):
                msg = self.msg_fmt % {'current_version': current_version,
                                      'new_version': new_version}
                log.warn(msg)
                return msg
            else:
                log.info('you are up to date')
        except Exception, error:
            log.error('failed while performing update check')
            log.exception(error)


def numeric(version):
    """Convert multi-part version string into a numeric value"""
    return sum(int(part) * (100 ** (2 - i))
               for i, part in enumerate(version.split('.'))
               if part.strip().isdigit())
