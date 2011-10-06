"""Memebot views"""

import os

from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from gruntle.memebot.decorators import login_or_apikey_required
from gruntle.memebot.models import UserProfile, Link
from gruntle.memebot.rss import get_feed_names, get_feeds
from gruntle.memebot.forms import CheckLinkForm
from gruntle.memebot.utils import text

@login_required
def view_index(request):
    """Site index"""
    return direct_to_template(request, 'memebot/index.html', {})


@login_required
def view_scores(request):
    """View scoreboard"""
    profiles = UserProfile.objects.get_by_score()
    return direct_to_template(request, 'memebot/scores.html', {'profiles': profiles})


@login_required
def browse_links(request):
    """Browse all links"""
    try:
        page = int(request.GET.get('page'))
    except StandardError:
        page = 1
    try:
        per_page = int(request.GET.get('per_page'))
    except StandardError:
        per_page = settings.BROWSE_LINKS_PER_PAGE

    start = (page - 1) * per_page
    end = start + per_page
    links = Link.objects.all()
    if not text.boolean(request.GET.get('disabled')):
        links = links.exclude(state='disabled')
    links = links.order_by('-created')[start:end]
    return direct_to_template(request, 'memebot/browse.html', {'links': links})


def _get_link(publish_id, **kwargs):
    """Helper function to get published links or raise 404"""
    return get_object_or_404(Link, publish_id=int(publish_id), state='published', **kwargs)


@login_required
def check_link(request):
    """Page to allow user to enter a URL to check its status"""
    if request.method == 'POST':
        form = CheckLinkForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(reverse('memebot-view-link', args=[form.cleaned_data['link'].publish_id]))

    else:
        form = CheckLinkForm()
    return direct_to_template(request, 'memebot/check-link.html', {'form': form})


@login_or_apikey_required
def view_link(request, publish_id):
    """Info about a link, TBD"""
    return direct_to_template(request, 'memebot/view-link.html', {'link': _get_link(publish_id)})


@login_or_apikey_required
def view_link_content(request, publish_id):
    """View generic published content that is cached locally"""
    link = _get_link(publish_id, content__isnull=False)
    return HttpResponse(link.content, link.content_type)


@login_or_apikey_required
def view_rss_index(request):
    """Index of available RSS feeds"""
    return direct_to_template(request, 'memebot/rss-index.html', {'feeds': get_feeds()})


@login_or_apikey_required
def view_rss(request, name):
    """View RSS feed"""
    if name not in get_feed_names():
        raise Http404
    feed_file = os.path.join(settings.FEED_DIR, name + '.xml')
    if not os.path.exists(feed_file):
        raise Http404
    with open(feed_file, 'r') as fp:
        return HttpResponse(fp.read(), 'application/rss+xml')
