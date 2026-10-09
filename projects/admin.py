from django.contrib import admin
from .models import Project, ProjectCategory, ProjectImage

@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    pass

# Shows the gallery as embedded rows on the project edit page.
class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    fields = ('image', 'caption', 'order')
    verbose_name = 'project photo'
    verbose_name_plural = 'project photos'
    extra = 1                      # one blank row for adding a new photo

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'category', 'order', 'is_featured', 'created_at')
    list_editable = ('order',)
    list_filter = ('category', 'is_featured')
    search_fields = ('title', 'client')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]
    list_select_related = ('category',)


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'caption', 'order')
    list_filter = ('project',)
    search_fields = ('project__title', 'caption')
    list_select_related = ('project',)
