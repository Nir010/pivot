from django.contrib import admin
from .models import SiteSettings, TeamMember, Service, Notice, SocialLink, ContactMessage

# The simplest way: just list the model. Admin builds an editor for it.
admin.site.register(SiteSettings)
admin.site.register(TeamMember)
admin.site.register(Notice)
admin.site.register(SocialLink)

# A "ModelAdmin" lets us customise HOW it's listed in the admin.
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_primary', 'order')
    list_filter = ('is_primary',)   # sidebar filter: primary vs other services
    list_editable = ('is_primary', 'order')   # toggle category + sort right in the list
    search_fields = ('title', 'summary', 'detail')
    ordering = ('order', 'title')

# A "ModelAdmin" lets us customise HOW it's listed in the admin.
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    # Messages arrive only through the Contact form — they are never created in the admin.
    def has_add_permission(self, request):
        return False

    list_display = ('name', 'email', 'organization', 'short_message', 'created_at', 'is_read')
    list_editable = ('is_read',)                 # tick/untick right in the list = read toggle
    list_filter = ('is_read',)                   # sidebar filter: read / unread
    search_fields = ('name', 'email', 'organization', 'message')
    readonly_fields = ('name', 'email', 'organization', 'message', 'created_at')
    actions = ['mark_read', 'mark_unread']

    @admin.action(description='Mark selected as read')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description='Mark selected as unread')
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)

    def short_message(self, obj):
        return obj.message[:80] + ('…' if len(obj.message) > 80 else '')
    short_message.short_description = 'Message'