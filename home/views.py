from django.contrib import messages
from django.shortcuts import (redirect,render,)  # fills a template with data and returns an HTTP response
from .models import (Notice, Service, ContactMessage, TeamMember)  # imports models.py within the same app
from .forms import ContactForm
import urllib.parse
import urllib.request
import threading

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
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            continue  # try the next endpoint; give up silently

# The home page. Shows an important-notice popup when one is ticked.
def home(request):  # view function
    # Fetch all active notices once; split important for popup (reduces queries)
    active_notices = list(Notice.objects.filter(is_active=True).order_by('-created_at'))
    important_notices = [n for n in active_notices if n.is_important]

    # Pass them to the template under the name "notices"
    return render(request, "home/index.html", {
        "notices": important_notices,
        "active_notices": active_notices,
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
        if not form.is_valid():
            messages.error(request, "Please fill in your name and a valid email.")
            return redirect("contact")

        cd = form.cleaned_data
        # 1) Always save to the database
        ContactMessage.objects.create(
            name=cd["name"], email=cd["email"],
            organization=cd["organization"], message=cd["message"],
        )
        # 2) Best-effort forward to Formspree.
        threading.Thread(
            target=_forward_to_formspree,
            args=(cd["name"], cd["email"], cd["organization"], cd["message"]),
            daemon=True,
        ).start()
        messages.success(request, "Thanks — your message has been sent.")
        return redirect("contact")

    return render(request, "home/contact.html")


def notices_list(request):
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'home/notices.html', {'notices': notices})
