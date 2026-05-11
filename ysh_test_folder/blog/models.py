from django.conf import settings
from django.db import models
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


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=90, unique=True, allow_unicode=True, blank=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=240, blank=True)
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    liked_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="PostLike",
        related_name="liked_posts",
        blank=True,
    )
    is_public = models.BooleanField(default=True)
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
