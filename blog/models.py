from django.db import models

# MODEL 1:
# A group that blog posts belong to, e.g. "Insurance", "Regulation".
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)   # URL-friendly: "insurance" not "Insurance"

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'  # admin shows "Categories", not "Categorys"

    def __str__(self):
        return self.name

    
# MODEL 2:
# One blog post / article.
class Post(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,        # delete category -> its posts go too
        related_name='posts',            # lets us do category.posts.all()
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True) # used in the URL, e.g. /blog/my-article/
    excerpt = models.TextField(blank=True)    # short teaser for listing cards
    body = models.TextField()                 # the full article
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='blog/pdfs/', blank=True, null=True)  # downloadable PDF
    is_pinned = models.BooleanField(default=False)    # pin to top of the blog page
    is_published = models.BooleanField(default=True)  # draft toggle
    created_at = models.DateTimeField(auto_now_add=True)  # set once
    updated_at = models.DateTimeField(auto_now=True)       # set on every save

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title