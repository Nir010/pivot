from django.test import TestCase
from django.urls import reverse

from .models import Category, Post


class BlogVisibilityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="News", slug="news")

    def test_draft_posts_not_shown_in_list(self):
        Post.objects.create(
            category=self.category,
            title="Draft post",
            slug="draft-post",
            body="Draft body",
            is_published=False,
        )
        response = self.client.get(reverse("blog_list"))
        self.assertNotContains(response, "Draft post")

    def test_published_posts_shown_in_list(self):
        Post.objects.create(
            category=self.category,
            title="Published post",
            slug="published-post",
            body="Published body",
            is_published=True,
        )
        response = self.client.get(reverse("blog_list"))
        self.assertContains(response, "Published post")

