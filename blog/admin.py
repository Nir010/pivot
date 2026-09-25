from django.contrib import admin
from .models import Category, Post

admin.site.register(Category)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_pinned', 'is_published', 'created_at')
    list_filter = ('category', 'is_pinned', 'is_published')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}   # auto-fill slug as you type the title