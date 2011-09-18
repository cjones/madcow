import urlparse
import urllib
import cgi
import re
import os

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm

from gruntle.memebot.exceptions import OldMeme

class Model(models.Model):

    class Meta:

        abstract = True

    created = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    modified = models.DateTimeField(auto_now=True, null=False, blank=False)


class Source(Model):

    SOURCE_TYPES = [('irc', 'IRC Chat Channel')]

    type = models.CharField(max_length=3, choices=SOURCE_TYPES, null=False, blank=False, default='irc')
    name = models.CharField(max_length=64, null=False, blank=False)

    class Meta:

        unique_together = 'type', 'name'

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.type)


class LinkManager(models.Manager):

    fragment_re = re.compile(r'^(.*)#([^;/?:@=&]*)$')

    def add_link(self, url, username, source_name, source_type, **kwargs):
        username = username.lower()
        user = Alias.objects.get_user(username)
        if user is None:
            if UserCreationForm.base_fields['username'].regex.search(username) is None:
                try:
                    user = User.objects.get(username=settings.UNKNOWN_USERNAME)
                except User.DoesNotExist:
                    user = self.create_anonymous_user(settings.UNKNOWN_USERNAME)
            else:
                user = self.create_anonymous_user(username)

        source = Source.objects.get_or_create(type=source_type, name=source_name)[0]
        normalized = self.normalize_url(url)

        try:
            link = self.get(normalized=normalized, source=source)
            if user != link.user:
                link.reposts += 1
                link.save()
                profile = user.get_profile()
                profile.posted_old += 1
                profile.save()
                poster_profile = link.user.get_profile()
                poster_profile.reposts += 1
                poster_profile.save()
                raise OldMeme(link)
        except self.model.DoesNotExist:
            link = self.create(user=user, source=source, url=url, normalized=normalized, **kwargs)
            profile = user.get_profile()
            profile.posted_new += 1
            profile.save()

        return link

    def create_anonymous_user(self, username):
        user = User.objects.create_user(username.lower(), settings.ANONYMOUS_USER_EMAIL)
        user.is_active = False
        user.save()
        return user

    def normalize_url(self, url):
        netloc = query = fragment = ''
        i = url.find(':')
        scheme = url[:i].lower()
        url = url[i+1:]
        if url[:2] == '//':
            delim = len(url)
            for c in '/?#':
                wdelim = url.find(c, 2)
                if wdelim >= 0:
                    delim = min(delim, wdelim)
            netloc, url = url[2:delim], url[delim:]
        if '#' in url:
            try:
                url, fragment = self.fragment_re.search(url).groups()
            except StandardError:
                pass
        if '?' in url:
            url, query = url.split('?', 1)

        netloc = netloc.lower()
        netloc = urlparse.unquote(netloc).replace('+', ' ')
        if netloc.startswith('www.') and len(netloc) > 4:
            netloc = netloc[4:]
        if netloc.endswith('.') and len(netloc) > 1:
            netloc = netloc[:-1]
        if url == '':
            url = '/'
        url = urlparse.unquote(url).replace('+', ' ')
        url = os.path.normpath(url)
        try:
            query = urllib.urlencode([item for item in sorted(cgi.parse_qsl(query)) if item[1]])
        except StandardError:
            query = ''
        return urlparse.urlunsplit((scheme, netloc, url, query, ''))


class Link(Model):

    objects = LinkManager()

    user = models.ForeignKey(User, null=False, blank=False, related_name='links')
    source = models.ForeignKey(Source, null=False, blank=False, related_name='links')

    url = models.TextField(null=False, blank=False)
    normalized = models.TextField(null=False, blank=False)
    reposts = models.IntegerField(null=False, blank=False, default=0)

    def __unicode__(self):
        return u'%s posted to %s (%s) by %s on %s (%d reposts)' % (
                self.url, self.source.name, self.source.get_type_display(),
                self.user.username, self.created.strftime('%Y-%m-%d %H:%M:%S'), self.reposts)

    class Meta:

        unique_together = 'normalized', 'source'


class Note(Model):

    user = models.ForeignKey(User, null=True, blank=True, related_name='notes')
    link = models.ForeignKey(Link, null=True, blank=True, related_name='notes')
    value = models.TextField(null=False, blank=False)

    class Meta:

        unique_together = 'link', 'value'


class AliasManager(models.Manager):

    def get_user(self, username):
        username = username.lower()
        try:
            user = self.get(username=username).user
        except self.model.DoesNotExist:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None
        return user

    def merge_user(self, old_user, new_user):
        if isinstance(old_user, (str, unicode)):
            old_user = User.objects.get(username=old_user.lower())
        if isinstance(new_user, (str, unicode)):
            new_user = User.objects.get(username=new_user.lower())
        alias = self.create(user=new_user, username=old_user.username)
        old_profile = old_user.get_profile()
        new_profile = new_user.get_profile()
        new_profile.posted_new += old_profile.posted_new
        new_profile.posted_old += old_profile.posted_old
        new_profile.reposts += old_profile.reposts
        new_profile.save()
        for link in old_user.links.all():
            link.user = new_user
            link.save()
        for note in old_user.notes.all():
            note.use = new_user
            note.save()
        old_user.delete()
        return alias


class Alias(Model):

    objects = AliasManager()

    user = models.ForeignKey(User, null=False, blank=False, related_name='aliases')
    username = models.CharField(max_length=30, null=False, blank=False, unique=True)

    def __unicode__(self):
        return u'%s -> %s' % (self.username, self.user.username)


class UserProfileManager(models.Manager):

    def get_by_score(self, *args, **kwargs):
        profiles = self.filter(*args, **kwargs)
        profiles = sorted(profiles, key=lambda profile: profile.sort_key)
        return profiles


class UserProfile(Model):

    MAXINT = 2 ** 31

    objects = UserProfileManager()

    user = models.ForeignKey(User, null=False, blank=False, unique=True)

    posted_new = models.IntegerField(null=False, blank=False, default=0)
    posted_old = models.IntegerField(null=False, blank=False, default=0)
    reposts = models.IntegerField(null=False, blank=False, default=0)

    def __unicode__(self):
        return u'Profile for %s' % self.user.username

    @property
    def sort_key(self):
        return self.MAXINT - self.score, self.user.username.lower()

    @property
    def score(self):
        return (self.posted_new * settings.MEMEBOT_POINTS_NEW +
                self.posted_old * settings.MEMEBOT_POINTS_OLD +
                self.reposts * settings.MEMEBOT_POINTS_REPOSTS)


def _create_profile(instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

models.signals.post_save.connect(_create_profile, sender=User, weak=False, dispatch_uid='create_profile')
