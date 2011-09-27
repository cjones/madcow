"""MemeBot Data Model"""

import datetime
import urlparse
import urllib
import cgi
import re
import os

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.conf import settings
from django.db import models

from gruntle.memebot.fields import SerializedDataField, PickleField, AttributeManager
from gruntle.memebot.exceptions import OldMeme

class Model(models.Model):

    """Abstract: Base model"""

    # for generating GUIDs
    _guid_fmt = 'tag:%(domain)s,%(date)s:/%(app)s/%(model)s/%(id)d/%(timestamp)s'
    _guid_id_fields = 'publish_id', 'external_id', 'id'

    # all models inherit these timestamps
    created = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    modified = models.DateTimeField(null=False, blank=False, auto_now=True)

    class Meta:

        abstract = True

    @property
    def guid(self):
        """Global unique identifier for this object"""
        site = Site.objects.get_current()
        model = type(self)
        for field in model._guid_id_fields:
            external_id = getattr(self, field, None)
            if external_id is not None:
                break
        else:
            raise TypeError('No suitable ID found for GUID creation')
        return model._guid_fmt % {
                'domain': site.domain,
                'date': self.created.strftime('%Y-%m-%d'),
                'app': model._meta.app_label,
                'model': model._meta.object_name.lower(),
                'id': external_id,
                'timestamp': self.created.strftime('%Y%m%d%H%M%S')}


class Source(Model):

    """Defines a URL source"""

    # valid locations
    SOURCE_TYPES = [('irc', 'IRC'),
                    ('web', 'Web')]

    # fields
    type = models.CharField(null=False, blank=False, max_length=16, choices=SOURCE_TYPES)
    name = models.CharField(null=False, blank=False, max_length=64)

    class Meta:

        unique_together = 'type', 'name'

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.type)


class LinkManager(models.Manager):

    """Custom object manager for Link model"""

    fragment_re = re.compile(r'^(.*)#([^;/?:@=&]*)$')

    def get_available(self):
        """Returns QuerySet of links available universally, ordered by creation date"""
        return self.exclude(state__in=('failed', 'hidden')).order_by('-created')

    def get_published(self):
        """Returns QuerySet of published links, ordered by publish date"""
        return self.filter(state='published').order_by('-published')

    @property
    def last_publish_id(self):
        published = self.filter(publish_id__isnull=False).only('publish_id').order_by('-publish_id')
        if published.count():
            return published[0].publish_id
        return 0

    def add_link(self, url, username, source_name, source_type, **kwargs):
        """
        Shortcut attempts to add the URL. Performs necessary
        normalizations, alias lookup, user creation, points assignment,
        etc. before trying to create the Link. Raises OldMeme(old_link)
        if a normalized version of this URL has been posted previously,
        otherwise returns the new Link.
        """
        username = username.lower()
        user = Alias.objects.get_user(username)
        if user is None:
            if settings.AUTO_USER_ADD and self.is_valid_username(username):
                user = self.create_anonymous_user(username)
            else:
                try:
                    user = User.objects.get(username=settings.UNKNOWN_USERNAME)
                except User.DoesNotExist:
                    user = self.create_anonymous_user(settings.UNKNOWN_USERNAME)

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
        """Create a new user that cannot login & fake email"""
        user = User.objects.create_user(username.lower(), settings.ANONYMOUS_USER_EMAIL)
        user.is_active = False
        user.save()
        return user

    def normalize_url(self, url):
        """Given a URL, try to normalize it such that we can find duplicate URLs more easily"""
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

    @staticmethod
    def is_valid_username(username):
        """True if the username is valid for django auth system"""
        return UserCreationForm.base_fields['username'].regex.search(username) is not None


class Link(Model):

    """Represents a posted URL"""

    # state of current link life-cycle
    LINK_STATES = [('new', 'New'),
                   ('invalid', 'Invalid'),
                   ('published', 'Published')]

    # custom object manager
    objects = LinkManager()

    # relationships
    user = models.ForeignKey(User, null=False, blank=False, related_name='links')
    source = models.ForeignKey(Source, null=False, blank=False, related_name='links')

    # basic url data
    url = models.TextField(null=False, blank=False)

    # memebot-related fields
    normalized = models.TextField(null=False, blank=False)
    reposts = models.IntegerField(null=False, blank=False, default=0)

    # content-discovery related fields
    state = models.CharField(null=False, blank=False, max_length=16, choices=LINK_STATES, default='new')
    error_count = models.IntegerField(null=False, blank=False, default=0)
    resolved_url = models.TextField(null=True, blank=True, default=None)
    content_type = models.CharField(null=True, blank=True, default=None, max_length=64)
    content = SerializedDataField(null=True, blank=True, default=None, engine='zlib', level=9)
    title = models.TextField(null=True, blank=True, default=None)
    published = models.DateTimeField(null=True, blank=True, default=None)
    publish_id = models.IntegerField(null=True, blank=True, default=None, unique=True)
    scanner = models.TextField(null=True, blank=True, default=None)
    attr_storage = PickleField(null=True, blank=True, default=None)
    attr = AttributeManager(storage_field='attr_storage')

    class Meta:

        unique_together = 'normalized', 'source'

    def __unicode__(self):
        return self.url

    def get_scanner(self):
        """Returns the real scanner object responsible for this links rendering"""
        if self.scanner:
            try:
                return __import__(self.scanner, globals(), locals(), ['scanner']).scanner
            except (ImportError, AttributeError):
                pass

    @property
    def rss_template(self):
        """The scanner-defined template used to render this link in RSS"""
        return self.get_scanner().rss_template

    @models.permalink
    def get_absolute_url(self):
        """URL to this links cached content"""
        if self.state == 'published' and self.content is not None:
            return ('content', [self.publish_id])

    absolute_url = property(get_absolute_url)

    @models.permalink
    def get_rss_url(self):
        """URL to this links RSS item"""
        if self.state == 'published':
            return ('view-rss', [self.publish_id])

    rss_url = property(get_rss_url)

    def publish(self, commit=True):
        """Publish this link"""
        dirty = False
        if self.state != 'published':
            self.state = 'published'
            dirty = True
        if self.published is None:
            self.published = datetime.datetime.now()
            dirty = True
        if self.publish_id is None:
            self.publish_id = Link.objects.last_publish_id + 1
            dirty = True
        if dirty and commit:
            self.save()
            dirty = False
        return dirty


class Note(Model):

    """A note associated with a link"""

    # relationships
    user = models.ForeignKey(User, null=True, blank=True, related_name='notes')
    link = models.ForeignKey(Link, null=True, blank=True, related_name='notes')

    # fields
    value = models.TextField(null=False, blank=False)

    class Meta:

        unique_together = 'user', 'link', 'value'


class AliasManager(models.Manager):

    """Custom object manager for Alias model"""

    def get_user(self, username):
        """Given a username, return the real user, after resolving aliases, or None"""
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
        """
        Given an old and new user (or name), merge the older's states
        into the newer, remove them, and create an alias pointing to the
        new user
        """
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

    """Represents a username alias, allowing a single person to receive credit under multiple names"""

    # custom objects manager
    objects = AliasManager()

    # relationships
    user = models.ForeignKey(User, null=False, blank=False, related_name='aliases')

    # fields
    username = models.CharField(null=False, blank=False, max_length=30, unique=True)

    def __unicode__(self):
        return u'%s -> %s' % (self.username, self.user.username)


class UserProfileManager(models.Manager):

    """Custom object manager for UserProfile model"""

    def get_by_score(self, *args, **kwargs):
        """Returns a list of profiles sorted by their calculated score"""
        profiles = self.filter(*args, **kwargs)
        profiles = sorted(profiles, key=lambda profile: profile.sort_key)
        return profiles


class UserProfile(Model):

    """A model for extra user data, such as posting stats"""

    MAXINT = 2 ** 31

    # custom object manager
    objects = UserProfileManager()

    # relationships
    user = models.ForeignKey(User, null=False, blank=False, unique=True)

    # memebot posting stats
    posted_new = models.IntegerField(null=False, blank=False, default=0)
    posted_old = models.IntegerField(null=False, blank=False, default=0)
    reposts = models.IntegerField(null=False, blank=False, default=0)

    def __unicode__(self):
        return u'Profile for %s' % self.user.username

    @property
    def sort_key(self):
        """This users cartesian sort key compared to other users, primary: score, secondary: name"""
        return self.MAXINT - self.score, self.user.username.lower()

    @property
    def score(self):
        """Calculated score for this user"""
        return (self.posted_new * settings.MEMEBOT_POINTS_NEW +
                self.posted_old * settings.MEMEBOT_POINTS_OLD +
                self.reposts * settings.MEMEBOT_POINTS_REPOSTS)


def _create_profile(instance, created, **kwargs):
    """Signal callback that creates a new profile when a new User object is created"""
    if created:
        UserProfile.objects.create(user=instance)


models.signals.post_save.connect(_create_profile, sender=User, weak=False, dispatch_uid='create_profile')
