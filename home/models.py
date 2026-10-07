from django.db import models
from pivot.ordering import ORDER_HELP_TEXT, OrderedModel
# MODEL 1:
# A single global settings row: everything about the company that appears on every page (branding, contact, socials, footer).
class SiteSettings(models.Model):
    site_name = models.TextField(blank=True)
    tagline = models.TextField(blank=True)
    address = models.TextField(blank=True)   # short address, shown in the footer
    contact_address = models.TextField(blank=True)  # detailed address, shown only on the Contact page
    email = models.EmailField(blank=True)   # general contact, shown on the Contact page
    phone = models.CharField(max_length=30, blank=True)
    email_2 = models.EmailField(blank=True)
    phone_2 = models.CharField(max_length=30, blank=True)
    # Department-wise contacts, shown in the footer under Contact.
    finance_hr_email = models.EmailField(blank=True)
    finance_hr_phone = models.CharField(max_length=30, blank=True)
    survey_email = models.EmailField(blank=True)
    survey_phone = models.CharField(max_length=30, blank=True)
    actuarial_email = models.EmailField(blank=True)
    actuarial_phone = models.CharField(max_length=30, blank=True)

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
class TeamMember(OrderedModel):
    ordering_scope = ('group',)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)   # e.g. "Managing Director"
    photo = models.ImageField(upload_to='team/', blank=True, null=True)

# leadership = the directors; members = the wider team
    GROUP_CHOICES = [('leadership', 'Leadership'), ('members', 'Members')]
    group = models.CharField(max_length=20, choices=GROUP_CHOICES, default='members')
    qualifications = models.TextField(blank=True)   # e.g. "MACS – Risk Analytics, BE Computer Engineering"
    experience = models.TextField(blank=True)       # one line per achievement, separated by newlines
    works = models.TextField(blank=True)            # major works, one per line
    order = models.PositiveIntegerField(default=0, help_text=ORDER_HELP_TEXT)

    class Meta:
        ordering = ['order', 'name']                      # sort by order, then name

    def __str__(self):
        return self.name


# MODEL 3:
# One row per service listed on the Services page.
class Service(OrderedModel):
    ordering_scope = ('is_primary',)
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)          # short blurb on cards
    detail = models.TextField(blank=True)           # longer description on the page
    is_primary = models.BooleanField(default=True)  # True = main grid, False = "Other services"
    order = models.PositiveIntegerField(default=0, help_text=ORDER_HELP_TEXT)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


# MODEL 4:
# One row per notice/announcement, e.g. shown on the home page.
class Notice(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to='notices/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='notices/pdfs/', blank=True, null=True)
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
