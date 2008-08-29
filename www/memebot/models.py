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

from django.db import models
from django.utils.html import escape

class Author(models.Model):
    name = models.TextField(unique=True)
    points_new = models.IntegerField(null=True, blank=True)
    points_old = models.IntegerField(null=True, blank=True)
    points_credit = models.IntegerField(null=True, blank=True)

    def getCount(self):
        count = self.url_set.count()
        return count

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'author'

    class Admin:
        pass

    count = property(getCount)


class Channel(models.Model):
    name = models.TextField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'channel'

    class Admin:
        pass


class URL(models.Model):
    url = models.TextField(unique=True)
    clean = models.TextField(unique=True)
    author = models.ForeignKey(Author)
    channel = models.ForeignKey(Channel)
    citations = models.IntegerField(null=True, blank=True)
    posted = models.DateTimeField('date posted')

    def getTimeStamp(self):
        return self.posted.strftime('%T')

    def getDateStamp(self):
        return self.posted.strftime('%F %T')

    def __str__(self):
        return self.url

    class Meta:
        db_table = 'url'

    class Admin:
        pass

    stamp = property(getTimeStamp)
    datestamp = property(getDateStamp)

class Comments(models.Model):
    text = models.TextField()
    author = models.ForeignKey(Author)
    url = models.ForeignKey(URL)

    def __str__(self):
        return self.text

    class Meta:
        db_table = 'comments'

    class Admin:
        pass

