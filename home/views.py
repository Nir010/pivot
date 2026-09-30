from django.contrib import messages
from django.shortcuts import (redirect,render,)  # fills a template with data and returns an HTTP response
from .models import (Notice, Service, ContactMessage, TeamMember)  # imports models.py within the same app
import urllib.parse
import urllib.request

FORMSPREE_ENDPOINTS = [
    "https://formspree.io/f/maenjyzw",
    "https://formspree.io/f/xzezgzql",
]

def _forward_to_formspree(name, email, organization, message):
    payload = urllib.parse.urlencode({
        "name": name,
        "email": email,
        "org": organization,
        "message": message,
        "_subject": f"Pivot Risk contact form: {name}",
        "_replyto": email,
    }).encode()
    for url in FORMSPREE_ENDPOINTS:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        urllib.request.urlopen(req, timeout=5)

# The home page. Shows an important-notice popup when one is ticked.
def home(request):  # view function
    # Fetch active AND important notices
    notices = Notice.objects.filter(is_active=True, is_important=True)

    # Pass them to the template under the name "notices"
    return render(request, "home/index.html", {"notices": notices})


# About page. Mostly fixed prose; the shared header/footer
def about(request):
    return render(request, "home/about.html")


# Services page: split into the main grid and the "Other services" grid.
def services(request):
    primary = Service.objects.filter(is_primary=True)  # main "Our Services" section
    others = Service.objects.filter(is_primary=False)  # collapsed "Other services" section
    return render(request, "home/services.html",{
            "primary_services": primary,
            "other_services": others,
        },
    )


# Team page: split the directors and the wider team for two separate grids.
def team(request):
    leadership = TeamMember.objects.filter(group="leadership")
    members = TeamMember.objects.filter(group="members")
    return render(request, "home/team.html",{
            "leadership": leadership,
            "members": members,
        },
    )


# Contact page: shows the form (GET) and saves submissions (POST).

def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        email = request.POST.get("email", "")
        organization = request.POST.get("org", "")
        message = request.POST.get("message", "")

        if not name or not email or "@" not in email:
            messages.error(request, "Please fill in your name and a valid email.")
            return redirect("contact")

        # 1) Always save to the database
        ContactMessage.objects.create(
            name=name,
            email=email,
            organization=organization,
            message=message,
        )

        # 2) Best-effort forward to Formspree.
        try:
            _forward_to_formspree(name, email, organization, message)
        except Exception:
            pass

        messages.success(request, "Thanks — your message has been sent.")
        return redirect("contact")

    return render(request, "home/contact.html")
