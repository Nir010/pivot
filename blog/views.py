from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils.html import strip_tags
from django.utils.text import Truncator
from .models import Post

# Blog listing: pinned posts first, then newest first.

def blog_list(request):
    posts = (
        Post.objects
        .filter(is_published=True)
        .select_related("category")
        .only(
            "id",
            "title",
            "slug",
            "excerpt",
            "cover_image",
            "pdf_file",
            "is_pinned",
            "created_at",
            "category__id",
            "category__name",
        )
        .order_by("-is_pinned", "-created_at", "-pk")
    )

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "blog/blog_list.html",
        {
            "posts": page_obj,
            "page_obj": page_obj,
        },
    )


# A single post, addressed by its slug in the URL (e.g. /blog/my-article/).
def blog_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related('category'), slug=slug, is_published=True)
    description = Truncator(strip_tags(post.excerpt or post.body)).chars(160)
    return render(
        request,
        'blog/blog_detail.html',
        {
            'post': post,
            'seo_title': f'{post.title} — Pivot Risk',
            'seo_description': description,
        },
    )