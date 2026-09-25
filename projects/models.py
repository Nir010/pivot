from django.db import models

# MODEL 1:
# A grouping for projects, e.g. "Governance".
class ProjectCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'project categories'

    def __str__(self):
        return self.name


# MODEL 2:
# One project shown on the Projects page.
class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.CASCADE,
        related_name='projects',
    )
    client = models.CharField(max_length=200, blank=True)   # who it was for
    summary = models.TextField(blank=True)                 # short card text
    detail = models.TextField(blank=True)                  # full page description
    thumbnail = models.ImageField(upload_to='projects/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)       # show on the home page
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title



# MODEL 3:
# One photo inside a project's gallery. 
# A project = one row in Project,
# but many rows here (via the ForeignKey).
class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='images',        # lets us do project.images.all()
    )
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.project.title} — {self.caption or 'photo'}"