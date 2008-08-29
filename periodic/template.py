
# XXX You should update this Copyright, but you must use a GPLv3 compatible
# license if you redistribute this with your modifications.

# Copyright (C) 2007, 2008 Christopher Jones
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

class Main(object):

    def __init__(self, madcow):
        self.madcow = madcow

        """
        Add a section in madcow.ini with appropriate defaults, like so:

        [modulename]
        enabled=no
        updatefreq=60
        channel=#madcow

        replacing "modulename" with a one-word descriptor of this module
        in both the ini header and the code below
        """

        self.enabled = madcow.config.modulename.enabled
        self.frequency = madcow.config.modulename.updatefreq
        self.output = madcow.config.modulename.channel

    def response(self, *args):
        """This is called by madcow, should return a string or None"""
