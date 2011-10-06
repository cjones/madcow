"""MemeBot context processors"""

from django.contrib.sites.models import Site
from django.conf import settings

current_site = Site.objects.get_current()

def site(request):
    """Add information about the site to template contexts"""
    return {'site_name': current_site.name,
            'site_domain': current_site.domain,
            'site_style': settings.STYLE_NAME}
