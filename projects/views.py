from django.shortcuts import get_object_or_404, render
from django.utils.html import strip_tags
from django.utils.text import Truncator
from .models import Project

# Project listing: featured projects first, then the rest.
def project_list(request):
    featured = Project.objects.filter(is_featured=True).select_related('category')
    others = Project.objects.filter(is_featured=False).select_related('category')
    return render(request, 'projects/project_list.html', {
        'featured_projects': featured,
        'other_projects': others,
    })


# A single project, by slug
def project_detail(request, slug):
    project = get_object_or_404(Project.objects.select_related('category').prefetch_related('images'), slug=slug)
    description = Truncator(
        strip_tags(project.summary or project.detail)
    ).chars(160)
    return render(
        request,
        'projects/project_detail.html',
        {
            'project': project,
            'seo_title': f'{project.title} — Pivot Risk',
            'seo_description': description,
        },
    )