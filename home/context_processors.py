from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import SiteSettings

CACHE_KEY = "site_settings:1"
# LocMemCache is per-process, so a save only clears the worker that handled the
# edit. A finite timeout bounds how long any other worker can serve stale data.
CACHE_TIMEOUT = 300  # seconds


def site_settings(request):
    settings = cache.get(CACHE_KEY)
    if settings is None:
        settings = SiteSettings.objects.filter(pk=1).first()
        cache.set(CACHE_KEY, settings, CACHE_TIMEOUT)
    return {"settings": settings}


@receiver([post_save, post_delete], sender=SiteSettings)
def _clear_site_settings_cache(sender, **kwargs):
    cache.delete(CACHE_KEY)