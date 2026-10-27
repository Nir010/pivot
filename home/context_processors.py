from django.conf import settings as django_settings
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


SEO_DEFAULTS = {
    "home": (
        "Pivot Risk Pvt. Ltd. — Risk Management & Advisory",
        "Risk management, actuarial, insurance and advisory services in Nepal.",
    ),
    "about": (
        "About Pivot Risk — Risk Management & Advisory",
        "Learn about Pivot Risk, a risk management and advisory firm based in Nepal.",
    ),
    "services": (
        "Services — Pivot Risk",
        "Explore Pivot Risk's risk management, actuarial, insurance and advisory services.",
    ),
    "team": (
        "Our Team — Pivot Risk",
        "Meet the team of risk management and advisory professionals at Pivot Risk.",
    ),
    "notices": (
        "Notices — Pivot Risk",
        "Read the latest announcements and notices from Pivot Risk.",
    ),
    "contact": (
        "Contact Pivot Risk",
        "Contact Pivot Risk for risk management, actuarial and advisory support.",
    ),
    "blog_list": (
        "Insights — Pivot Risk",
        "Read insights, updates and articles from Pivot Risk.",
    ),
    "project_list": (
        "Projects — Pivot Risk",
        "Explore projects delivered by Pivot Risk across risk management and advisory.",
    ),
}


def seo(request):
    resolver_match = getattr(request, "resolver_match", None)
    view_name = getattr(resolver_match, "url_name", None)
    title, description = SEO_DEFAULTS.get(
        view_name,
        ("Pivot Risk Pvt. Ltd.", "Risk management and advisory services in Nepal."),
    )
    return {
        "seo_title": title,
        "seo_description": description,
        "canonical_url": f"{django_settings.SITE_URL}{request.path}",
    }


@receiver([post_save, post_delete], sender=SiteSettings)
def _clear_site_settings_cache(sender, **kwargs):
    cache.delete(CACHE_KEY)