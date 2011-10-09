"""View functions for root of site"""

from django.views.generic.simple import direct_to_template
from django.http import HttpResponse, Http404

def view_index(request):
    """Front page"""
    return direct_to_template(request, 'root/index.html', {})


def view_robots(request):
    """View the site robots.txt file"""
    return direct_to_template(request, 'root/robots.txt', mimetype='text/plain')


def friendly_404(request):
    """Raise 404 normally, uses 404.html template with site style"""
    raise Http404


def harsh_404(request):
    """Spartan 404 that reveaals notthing about the site, used when people are digging"""
    return HttpResponse('no.', 'text/plain', 404)
