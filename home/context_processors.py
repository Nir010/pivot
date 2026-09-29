from .models import SiteSettings

# Injects the single global settings row into every template as {{ settings }}.
def site_settings(request):
    return {
        'settings': SiteSettings.objects.first(),
    }