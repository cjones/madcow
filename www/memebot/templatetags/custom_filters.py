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

from django import template
from django.utils.html import escape

register = template.Library()

@register.filter("safelink")
def safelink(url, limit=None):
    url = str(url)
    size = len(url)
    url = escape(url)

    link = '<a href="%s" target="_new">' % url

    if limit is not None and size > limit:
        url = url[:limit] + '...' + url[-4:]

    return '%s%s</a>' % (link, url)
