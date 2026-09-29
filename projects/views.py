from django.shortcuts import get_object_or_404, render
from .models import Project

# Project listing: all projects, newest first.
def project_list(request):
    projects = Project.objects.all()
    return render(request, 'projects/project_list.html', {'projects': projects})


# A single project, by slug
def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    return render(request, 'projects/project_detail.html', {'project': project})