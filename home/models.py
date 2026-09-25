from django.db import models
# MODEL 1:
# A single global settings row: everything about the company that appears on every page (branding, contact, socials, footer).
class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Force this row to always be the one with id=1.
        # Creating a "second" settings row just overrides the first — so
        # a duplicate can never exist.
        self.pk = 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.site_name


# MODEL 2:
# One row per team member shown on the Team page.
# Photos are uploaded through the admin and stored in MEDIA_ROOT.
class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)   # e.g. "Managing Director"
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    bio = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)        # sort position on the page

    class Meta:
        ordering = ['order', 'name']                      # sort by order, then name

    def __str__(self):
        return self.name


# MODEL 3:
# One row per service listed on the Services page.
class Service(models.Model):
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)          # short blurb on cards
    detail = models.TextField(blank=True)           # longer description on the page
    icon_class = models.CharField(max_length=100, blank=True)  # CSS class for the icon
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


# MODEL 4:
# One row per notice/announcement, e.g. shown on the home page.
class Notice(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)   # show it or not
    is_important = models.BooleanField(default=False)  # if True, shows as a home-page popup
    created_at = models.DateTimeField(auto_now_add=True)  # set once, on creation

    class Meta:
        ordering = ['-created_at']                  # newest first

    def __str__(self):
        return self.title
    


# MODEL 5:
# One row per social profile shown in the site's footer/header.
class SocialLink(models.Model):
    platform = models.CharField(max_length=50)      # e.g. "LinkedIn"
    url = models.URLField()                         # Web address — validates it starts with http(s)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'platform']

    def __str__(self):
        return self.platform



# MODEL 6:
# One row per message submitted through the Contact form.
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    organization = models.CharField(max_length=150, blank=True)  # matches form's "org" field
    message = models.TextField()
    is_read = models.BooleanField(default=False)    # handled/unhandled toggle in admin
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.email}"