"""View functions for root of site"""

from django.views.generic.simple import direct_to_template

def view_index(request):
    """Front page"""
    return direct_to_template(request, 'root/index.html', {})
