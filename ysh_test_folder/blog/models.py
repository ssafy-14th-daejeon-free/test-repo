from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils.text import Truncator, slugify

from .utils import render_markdown


def build_unique_slug(model, value, instance_pk=None, max_length=90):
    base = slugify(value, allow_unicode=True)[:max_length].strip("-") or "post"
    slug = base
    index = 2
    queryset = model.objects.all()

    while queryset.filter(slug=slug).exclude(pk=instance_pk).exists():
        suffix = f"-{index}"
        slug = f"{base[: max_length - len(suffix)]}{suffix}"
        index += 1

    return slug


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(max_length=40, unique=True, allow_unicode=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Tag, self.name, self.pk, max_length=40)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("tag_posts", kwargs={"slug": self.slug})


class Series(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="series",
    )
    title = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True, allow_unicode=True, blank=True)
    description = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "series"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Series, self.title, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("series_posts", kwargs={"slug": self.slug})


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=90, unique=True, allow_unicode=True, blank=True)
    cover_url = models.URLField(blank=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=240, blank=True)
    series = models.ForeignKey(
        Series,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
    )
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="PostLike",
        related_name="liked_posts",
        blank=True,
    )
    is_public = models.BooleanField(default=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = build_unique_slug(Post, self.title, self.pk)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    @property
    def rendered_content(self):
        return render_markdown(self.content)

    @property
    def summary(self):
        if self.excerpt:
            return self.excerpt
        return Truncator(self.content.replace("#", "").strip()).chars(180)

    def like_count(self):
        return self.likes.count()

    def record_view(self):
        Post.objects.filter(pk=self.pk).update(view_count=F("view_count") + 1)
        self.refresh_from_db(fields=["view_count"])


class PostLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_post_like")
        ]

    def __str__(self):
        return f"{self.user} likes {self.post}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_links",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"],
                name="unique_local_follow",
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("following")),
                name="prevent_self_follow",
            ),
        ]

    def __str__(self):
        return f"{self.follower} follows {self.following}"


class Notification(models.Model):
    class Kind(models.TextChoices):
        FOLLOW = "follow", "Follow"
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"
        SYSTEM = "system", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        blank=True,
        null=True,
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="notifications",
        blank=True,
        null=True,
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    message = models.CharField(max_length=180)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
