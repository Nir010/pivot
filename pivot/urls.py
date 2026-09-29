from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),            # /, /about/, /services/, /team/, /contact/
    path('blog/', include('blog.urls')),       # /blog/, /blog/<slug>/
    path('projects/', include('projects.urls')),  # /projects/, /projects/<slug>/
]

# Development only: serve files users uploaded (media/) at the /media/ URL.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)