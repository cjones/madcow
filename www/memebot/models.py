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

