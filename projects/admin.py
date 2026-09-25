from django.contrib import admin
from .models import Project, ProjectCategory, ProjectImage

@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    pass

# Shows the gallery as embedded rows on the project edit page.
class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1                      # one blank row for adding a new photo

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'category', 'is_featured', 'created_at')
    list_filter = ('category', 'is_featured')
    search_fields = ('title', 'client')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]