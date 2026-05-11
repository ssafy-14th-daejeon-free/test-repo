from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Post, PostLike, Tag
from .utils import render_markdown


class PostModelTests(TestCase):
    def test_post_slug_is_unique(self):
        author = User.objects.create_user("author", password="pass")
        first = Post.objects.create(author=author, title="Same Title", content="Body")
        second = Post.objects.create(author=author, title="Same Title", content="Body")

        self.assertEqual(first.slug, "same-title")
        self.assertEqual(second.slug, "same-title-2")

    def test_markdown_output_strips_unsafe_html_and_protocols(self):
        rendered = render_markdown("[bad](javascript:alert(1))<script>alert(1)</script>")

        self.assertNotIn("javascript:", rendered)
        self.assertNotIn("<script", rendered)
        self.assertIn("<a>bad</a>", rendered)


class PostViewTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user("author", password="StrongPass123!")
        self.other = User.objects.create_user("other", password="StrongPass123!")
        self.post = Post.objects.create(
            author=self.author,
            title="First Post",
            content="# Hello\n\nBody text.",
        )
        self.tag = Tag.objects.create(name="django")
        self.post.tags.add(self.tag)

    def test_public_post_list_and_detail_render(self):
        list_response = self.client.get(reverse("post_list"))
        detail_response = self.client.get(reverse("post_detail", args=[self.post.slug]))

        self.assertContains(list_response, "First Post")
        self.assertContains(detail_response, "<h1>Hello</h1>", html=True)

    def test_search_filters_posts(self):
        Post.objects.create(author=self.author, title="Another Topic", content="Body")

        response = self.client.get(reverse("post_list"), {"q": "First"})

        self.assertContains(response, "First Post")
        self.assertNotContains(response, "Another Topic")

    def test_login_required_for_create(self):
        response = self.client.get(reverse("post_create"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_author_can_create_post_with_tags(self):
        self.client.login(username="author", password="StrongPass123!")

        response = self.client.post(
            reverse("post_create"),
            {
                "title": "New Post",
                "content": "Content",
                "excerpt": "Summary",
                "tags_text": "django, clone",
                "is_public": "on",
            },
        )

        post = Post.objects.get(title="New Post")
        self.assertRedirects(response, post.get_absolute_url())
        self.assertEqual(list(post.tags.values_list("name", flat=True)), ["clone", "django"])

    def test_only_author_can_update_or_delete(self):
        self.client.login(username="other", password="StrongPass123!")

        update_response = self.client.post(
            reverse("post_update", args=[self.post.slug]),
            {
                "title": "Changed",
                "content": "Changed content",
                "excerpt": "",
                "tags_text": "",
                "is_public": "on",
            },
        )
        delete_response = self.client.post(reverse("post_delete", args=[self.post.slug]))

        self.assertEqual(update_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "First Post")

    def test_like_toggle_is_unique(self):
        self.client.login(username="other", password="StrongPass123!")
        url = reverse("post_like", args=[self.post.slug])

        first = self.client.post(url)
        second = self.client.post(url)

        self.assertRedirects(first, self.post.get_absolute_url())
        self.assertRedirects(second, self.post.get_absolute_url())
        self.assertEqual(PostLike.objects.filter(post=self.post, user=self.other).count(), 0)

    def test_tag_page_lists_matching_posts(self):
        response = self.client.get(reverse("tag_posts", args=[self.tag.slug]))

        self.assertContains(response, "#django")
        self.assertContains(response, "First Post")
