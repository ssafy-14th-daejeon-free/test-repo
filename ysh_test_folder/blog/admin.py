from django.contrib import admin

from .models import Comment, Post, PostLike, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "is_public", "created_at", "updated_at")
    list_filter = ("is_public", "created_at", "tags")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "content", "author__username")
    filter_horizontal = ("tags",)


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__title")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "author", "created_at")
    search_fields = ("post__title", "author__username", "content")

# Register your models here.
