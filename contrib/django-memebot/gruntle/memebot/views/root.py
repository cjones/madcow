"""View functions for root of site"""

from django.views.generic.simple import direct_to_template

def view_index(request):
    """Front page"""
    return direct_to_template(request, 'root/index.html', {})


def view_robots(request):
    """View the site robots.txt file"""
    return direct_to_template(request, 'root/robots.txt', mimetype='text/plain')
