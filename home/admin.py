from django.contrib import admin
from .models import SiteSettings, TeamMember, Service, Notice, SocialLink, ContactMessage

# The simplest way: just list the model. Admin builds an editor for it.
admin.site.register(SiteSettings)
admin.site.register(TeamMember)
admin.site.register(Service)
admin.site.register(Notice)
admin.site.register(SocialLink)

# A "ModelAdmin" lets us customise HOW it's listed in the admin.
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'organization', 'is_read', 'created_at')
    list_filter = ('is_read',)                 # sidebar filter: read / unread
    readonly_fields = ('name', 'email', 'organization', 'message', 'created_at')