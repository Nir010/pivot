import logging

from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (redirect,render,)  # fills a template with data and returns an HTTP response
from django.urls import reverse
from .models import (Notice, Service, ContactMessage, TeamMember)  # imports models.py within the same app
from .forms import ContactForm
from blog.models import Post
from projects.models import Project

logger = logging.getLogger(__name__)


def _wants_json(request):
    """True when the request came from our fetch() handler (AJAX)."""
    return (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or "application/json" in request.headers.get("accept", "")
    )

# The home page. Shows an important-notice popup when one is ticked.
def home(request):  # view function
    important_notices = Notice.objects.filter(
        is_active=True,
        is_important=True,
    ).order_by("order", "-created_at", "-pk")

    # Pass them to the template under the name "notices"
    return render(request, "home/index.html", {
        "notices": important_notices,
    })


# About page. Mostly fixed prose; the shared header/footer
def about(request):
    return render(request, "home/about.html")


# Services page: split into the main grid and the "Other services" grid.
def services(request):
    primary = Service.objects.filter(is_primary=True).order_by('order', 'title')  # main "Our Services" section
    others = Service.objects.filter(is_primary=False).order_by('order', 'title')  # collapsed "Other services" section
    return render(request, "home/services.html",{
            "primary_services": primary,
            "other_services": others,
        },
    )


# Team page: split the directors and the wider team for two separate grids.
def team(request):
    leadership = TeamMember.objects.filter(group="leadership").order_by('order', 'name')
    members = TeamMember.objects.filter(group="members").order_by('order', 'name')
    return render(request, "home/team.html",{
            "leadership": leadership,
            "members": members,
        },
    )


# Contact page: shows the form (GET) and saves submissions (POST).

def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Save the message; the browser also forwards it to Formspree.
            ContactMessage.objects.create(
                name=cd["name"], email=cd["email"],
                organization=cd["organization"], message=cd["message"],
            )
            logger.info("Contact message saved from %s <%s>", cd["name"], cd["email"])
            if _wants_json(request):
                return JsonResponse({"ok": True, "message": "Thanks — your message has been sent."})
            messages.success(request, "Thanks — your message has been sent.")
            return redirect("contact")
        # Invalid: re-render with the errors + typed values (don't redirect).
        logger.warning("Invalid contact submission: %s", form.errors.as_json())
        if _wants_json(request):
            errors = {
                field: [entry["message"] for entry in entries]
                for field, entries in form.errors.get_json_data().items()
            }
            return JsonResponse({"ok": False, "errors": errors}, status=400)
        messages.error(request, "Please correct the highlighted fields below.")
    else:
        form = ContactForm()

    return render(request, "home/contact.html", {"form": form})


def notices_list(request):
    notices = Notice.objects.filter(is_active=True).order_by('order', '-created_at', '-pk')
    return render(request, 'home/notices.html', {'notices': notices})


def sitemap(request):
    paths = [
        reverse(name)
        for name in (
            "home",
            "about",
            "services",
            "team",
            "notices",
            "contact",
            "blog_list",
            "project_list",
        )
    ]
    paths.extend(
        reverse("blog_detail", args=[post.slug])
        for post in Post.objects.filter(is_published=True).only("slug")
    )
    paths.extend(
        reverse("project_detail", args=[project.slug])
        for project in Project.objects.only("slug")
    )
    return render(
        request,
        "home/sitemap.xml",
        {"site_url": settings.SITE_URL, "paths": paths},
        content_type="application/xml",
    )


def robots(request):
    sitemap_url = f"{settings.SITE_URL}{reverse('sitemap')}"
    return HttpResponse(
        f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {sitemap_url}\n",
        content_type="text/plain",
    )
