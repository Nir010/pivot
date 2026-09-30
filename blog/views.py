from django.shortcuts import get_object_or_404, render
from .models import Post

# Blog listing: pinned posts first, then newest first.
def blog_list(request):
    posts = Post.objects.filter(is_published=True).order_by('-is_pinned', '-created_at')
    return render(request, 'blog/blog_list.html', {'posts': posts})


# A single post, addressed by its slug in the URL (e.g. /blog/my-article/).
def blog_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    return render(request, 'blog/blog_detail.html', {'post': post})