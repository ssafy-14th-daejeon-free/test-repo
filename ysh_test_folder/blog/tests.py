from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Comment, Follow, Notification, Post, PostLike, Series, Tag
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
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, 1)

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
                "cover_url": "https://example.com/cover.jpg",
                "content": "Content",
                "excerpt": "Summary",
                "series_title": "Django Notes",
                "tags_text": "django, clone",
                "is_public": "on",
            },
        )

        post = Post.objects.get(title="New Post")
        self.assertRedirects(response, post.get_absolute_url())
        self.assertEqual(post.cover_url, "https://example.com/cover.jpg")
        self.assertEqual(list(post.tags.values_list("name", flat=True)), ["clone", "django"])
        self.assertEqual(post.series.title, "Django Notes")

    def test_author_can_save_local_draft(self):
        self.client.login(username="author", password="StrongPass123!")

        response = self.client.post(
            reverse("post_create"),
            {
                "title": "Draft Post",
                "content": "Draft content",
                "excerpt": "",
                "series_title": "",
                "tags_text": "",
                "action": "draft",
            },
        )

        draft = Post.objects.get(title="Draft Post")
        self.assertRedirects(response, draft.get_absolute_url())
        self.assertFalse(draft.is_public)

        drafts_response = self.client.get(reverse("draft_list"))
        self.assertContains(drafts_response, "Draft Post")

    def test_feed_tab_uses_followed_authors(self):
        followed = User.objects.create_user("followed", password="StrongPass123!")
        Post.objects.create(author=followed, title="Followed Post", content="Body")
        Follow.objects.create(follower=self.other, following=followed)
        self.client.login(username="other", password="StrongPass123!")

        response = self.client.get(reverse("post_list"), {"tab": "feed"})

        self.assertContains(response, "Followed Post")
        self.assertNotContains(response, "First Post")

    def test_series_page_lists_matching_posts(self):
        series = Series.objects.create(author=self.author, title="Learning Django")
        self.post.series = series
        self.post.save(update_fields=["series"])

        response = self.client.get(reverse("series_posts", args=[series.slug]))

        self.assertContains(response, "Learning Django")
        self.assertContains(response, "First Post")

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

    def test_logged_in_user_can_comment(self):
        self.client.login(username="other", password="StrongPass123!")

        response = self.client.post(
            reverse("comment_create", args=[self.post.slug]),
            {"content": "Great post."},
        )

        self.assertRedirects(response, self.post.get_absolute_url())
        self.assertEqual(Comment.objects.get(post=self.post).content, "Great post.")
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.author,
                actor=self.other,
                kind=Notification.Kind.COMMENT,
            ).exists()
        )

    def test_only_comment_or_post_author_can_delete_comment(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.other,
            content="Please remove later.",
        )
        stranger = User.objects.create_user("stranger", password="StrongPass123!")
        self.client.login(username="stranger", password="StrongPass123!")

        forbidden = self.client.post(reverse("comment_delete", args=[comment.pk]))
        self.assertEqual(forbidden.status_code, 403)

        self.client.login(username="author", password="StrongPass123!")
        allowed = self.client.post(reverse("comment_delete", args=[comment.pk]))

        self.assertRedirects(allowed, self.post.get_absolute_url())
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_stats_dashboard_shows_local_counts(self):
        PostLike.objects.create(post=self.post, user=self.other)
        Comment.objects.create(post=self.post, author=self.other, content="Nice.")
        self.post.view_count = 3
        self.post.save(update_fields=["view_count"])
        self.client.login(username="author", password="StrongPass123!")

        response = self.client.get(reverse("stats_dashboard"))

        self.assertContains(response, "3")
        self.assertContains(response, "1 likes")
        self.assertContains(response, "1 comments")
