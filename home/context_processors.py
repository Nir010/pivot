from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import SiteSettings

CACHE_KEY = "site_settings:1"


def site_settings(request):
    settings = cache.get(CACHE_KEY)
    if settings is None:
        try:
            settings = SiteSettings.objects.get(pk=1)
        except SiteSettings.DoesNotExist:
            settings = None
        cache.set(CACHE_KEY, settings, None)  # cache indefinitely
    return {"settings": settings}


@receiver([post_save, post_delete], sender=SiteSettings)
def _clear_site_settings_cache(sender, **kwargs):
    cache.delete(CACHE_KEY)