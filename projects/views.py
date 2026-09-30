from django.shortcuts import get_object_or_404, render
from .models import Project

# Project listing: featured projects first, then the rest.
def project_list(request):
    featured = Project.objects.filter(is_featured=True)
    others = Project.objects.filter(is_featured=False)
    return render(request, 'projects/project_list.html', {
        'featured_projects': featured,
        'other_projects': others,
    })


# A single project, by slug
def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    return render(request, 'projects/project_detail.html', {'project': project})