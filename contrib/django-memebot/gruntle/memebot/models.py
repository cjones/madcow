"""MemeBot Data Model"""

'''
SETTINGS:
- max bytes to fetch on initial request to determine content type/link state.. keep pretty low
- max transient errors before giving up on this link (keep low? maybe use back-of approach instead of burn fast)
- max redirects when resolving a url.. find out what typical failure threshold is for this
- (bool) download images or hotlink?
- (bool) try to generate text summary? use title/url otherwise
- list of scanners to run besides the default

STATES:
[new] just posted.. available to memebot and browse page if in raw mode
-> processor picks up [new,deferred]
[processing] same availability as [new]. during this time, processor will do things:
    - try to actually fetch the url: headers and first <n> bytes
    - if a transient error occurs (5xx), bump <fail_count> field. if <max fails>, put into [failed] and set
      <error>, for the record, otherwise place into [deferred]
    - if a fatal error (4xx), fail immediately.
    - if a redirect (3xx), follow redirects until a non-redirect, loop, or <max redirects> is hit,
      save the final url to <resolved_url> if we have something to save
    - if OK status, check headers for & save <mime_type>, then:
        - if media we want to cache (just images for now), fetch [up to <max binary size>], serialize as
          base64 and store in content field.
        - articles should cache a summary paragraph if possible. Maybe Readability could help here. it can go
          in Content field too (with text/html mime_type) if feasible, otherwise make <summary> field.
        - a way to have extensible special handlers.. for example, a youtube.py module will know how to take
          a youtube link and create embeddable content from the url, rather than scraping it naively.
        - Store title in <title> field if it exists
        - be sure to decode any text data with the real encoding of the page (check meta, http header, decl first)
        - set <published> to the time it finally finished processing succesffully so that in rss, it comes
          out in order. if we use the date we found the url, stuff that gets differed will get posted later but 
          with back-dated publish field
        - finally, set state to [published]

[deferred] like new, just indicates its already been worked on once and had a temporary problem
[published] shows up everywhere and ordered by published. These have available to them any of:
    - A full title
    - The *real* URL shorteners point to, which we should use (Q: check against these for oldmemes somehow?)
    - Its MIME type
    - Pre-cached stuff in content field we can put in the feed: actual image, youtube embed, article summary, etc.
    - The date we "published" (finished processing) the link

[hidden] field we can use to pull a URL from being displayed anywhere without actually deleting it.. probably
         it should not count against you for memepoints either. what should it do though? it can't save it.. if
         someone reposts it and then checks if it saved via someone else posting it, the lack of error will
         leak that it's in the DB but hidden.. may be seen as a bug? maybe not a big deal.
'''

import urlparse
import urllib
import cgi
import re
import os

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.conf import settings
from django.db import models

from gruntle.memebot.exceptions import OldMeme
from gruntle.memebot.fields import SerializedDataField

class Model(models.Model):

    """Abstract: Base model"""

    created = models.DateTimeField(null=False, blank=False, auto_now_add=True)
    modified = models.DateTimeField(null=False, blank=False, auto_now=True)

    class Meta:

        abstract = True


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

    def get_ready(self):
        """Returns QuerySet of links that are ready for processing"""
        raise NotImplementedError

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
    LINK_STATES = [('new', 'Newly Posted'),
                   ('processing', 'Being Processed'),
                   ('deferred', 'Deferred To Next Run'),
                   ('failed', 'Failed To Validate'),
                   ('published', 'Published'),
                   ('hidden', 'Hidden')]

    # hint for views about what is in the content field
    LINK_CONTENT_TYPES = [('image', 'Image Data'),           # content is raw image data to be displayed in-line
                          ('summary', 'Summary Text'),       # content is a text paragraph from an article/blog/essay
                          ('rendered', 'Pre-Rendered HTML'), # hint from scanner, indicates content is already rendered
                          ('error', 'Error Message')]        # why this link could not validate, text

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
    mime_type = models.CharField(null=True, blank=True, default='text/plain', max_length=64)
    content_type = models.CharField(null=True, blank=True, default=None, max_length=16, choices=LINK_CONTENT_TYPES)
    content = SerializedDataField(null=True, blank=True, default=None, engine='zlib', level=9)
    title = models.TextField(null=True, blank=True, default=None)
    published = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:

        unique_together = 'normalized', 'source'

    def __unicode__(self):
        return self.url


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
