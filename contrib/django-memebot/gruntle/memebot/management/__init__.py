from django.contrib.sites import models as sites_app
from django.db.models import signals
from django.conf import settings

DEFAULT_DOMAIN = 'gruntle.org'
DEFAULT_NAME = 'MemeBot'

def set_site(created_models, interactive, **kwargs):
    if sites_app.Site in created_models:
        domain = DEFAULT_DOMAIN
        name = DEFAULT_NAME
        if interactive:
            domain = raw_input('Site domain [%s]: ' % domain) or domain
            name = raw_input('Site name [%s]: ' % name) or name
        site, created = sites_app.Site.objects.get_or_create(id=settings.SITE_ID)
        site.domain = domain
        site.name = name
        site.save()
        sites_app.Site.objects.clear_cache()

signals.post_syncdb.connect(set_site, sender=sites_app, dispatch_uid='set_site')
