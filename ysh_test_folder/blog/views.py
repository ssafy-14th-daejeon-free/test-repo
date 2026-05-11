from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Notification, Post, PostLike, Series, Tag


FEED_TABS = [
    ("trending", "Trending"),
    ("recommended", "Recommended"),
    ("latest", "Latest"),
    ("feed", "Feed"),
]


def public_posts():
    return (
        Post.objects.filter(is_public=True)
        .select_related("author", "series")
        .prefetch_related("tags", "likes")
        .annotate(likes_count=Count("likes"))
    )


def ordered_posts(queryset, tab):
    if tab == "latest" or tab == "feed":
        return queryset.order_by("-created_at")
    if tab == "recommended":
        return queryset.order_by("-likes_count", "-updated_at")
    return queryset.order_by("-likes_count", "-created_at")


def paginate(request, queryset, per_page=12):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def post_list(request):
    active_tab = request.GET.get("tab", "trending")
    if active_tab not in {key for key, _ in FEED_TABS}:
        active_tab = "trending"

    search_query = request.GET.get("q", "").strip()
    posts = public_posts()
    if active_tab == "feed" and request.user.is_authenticated:
        followed_ids = Follow.objects.filter(follower=request.user).values("following_id")
        posts = posts.filter(author_id__in=followed_ids)

    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(tags__name__icontains=search_query)
            | Q(series__title__icontains=search_query)
        ).distinct()

    return render(
        request,
        "blog/post_list.html",
        {
            "page_title": "Search" if search_query else "Trending",
            "page_obj": paginate(request, ordered_posts(posts, active_tab)),
            "tabs": FEED_TABS,
            "active_tab": active_tab,
            "search_query": search_query,
            "tags": Tag.objects.all()[:20],
        },
    )


def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = ordered_posts(public_posts().filter(tags=tag), "latest")
    return render(
        request,
        "blog/post_list.html",
        {
            "page_title": f"#{tag.name}",
            "page_obj": paginate(request, posts),
            "tabs": FEED_TABS,
            "active_tab": "latest",
            "active_tag": tag,
            "tags": Tag.objects.all()[:20],
        },
    )


def series_posts(request, slug):
    series = get_object_or_404(Series.objects.select_related("author"), slug=slug)
    posts = ordered_posts(public_posts().filter(series=series), "latest")
    return render(
        request,
        "blog/post_list.html",
        {
            "page_title": series.title,
            "page_obj": paginate(request, posts),
            "tabs": FEED_TABS,
            "active_tab": "latest",
            "series": series,
            "tags": Tag.objects.all()[:20],
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("author", "series").prefetch_related(
            "tags", "likes", "comments"
        ),
        slug=slug,
    )
    if not post.is_public and post.author != request.user:
        raise Http404("Post not found.")
    post.record_view()

    liked = False
    if request.user.is_authenticated:
        liked = post.likes.filter(user=request.user).exists()

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "liked": liked,
            "can_edit": request.user == post.author,
            "comments": post.comments.select_related("author"),
            "comment_form": CommentForm(),
        },
    )


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            if request.POST.get("action") == "draft":
                post.is_public = False
            elif request.POST.get("action") == "publish":
                post.is_public = True
            post.save()
            form.save_tags(post)
            form.save_series(post)
            if post.is_public:
                messages.success(request, "Post published.")
            else:
                messages.success(request, "Draft saved in local SQLite storage.")
            return redirect(post)
    else:
        form = PostForm()

    return render(
        request,
        "blog/post_form.html",
        {"form": form, "page_title": "Write", "submit_label": "Publish"},
    )


@login_required
def post_update(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.author != request.user:
        return HttpResponseForbidden("Only the author can edit this post.")

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            if request.POST.get("action") == "draft":
                post.is_public = False
            elif request.POST.get("action") == "publish":
                post.is_public = True
            post.save()
            form.save_tags(post)
            form.save_series(post)
            if post.is_public:
                messages.success(request, "Post published.")
            else:
                messages.success(request, "Draft saved in local SQLite storage.")
            return redirect(post)
    else:
        form = PostForm(instance=post)

    return render(
        request,
        "blog/post_form.html",
        {"form": form, "post": post, "page_title": "Edit", "submit_label": "Save"},
    )


@login_required
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.author != request.user:
        return HttpResponseForbidden("Only the author can delete this post.")

    if request.method == "POST":
        post.delete()
        messages.success(request, "Post deleted.")
        return redirect("post_list")

    return render(request, "blog/post_confirm_delete.html", {"post": post})


@login_required
@require_POST
def toggle_like(request, slug):
    post = get_object_or_404(Post, slug=slug, is_public=True)
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    if created:
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                post=post,
                kind=Notification.Kind.LIKE,
                message=f"{request.user.username} liked your post.",
            )
    else:
        like.delete()
    return redirect(post)


@login_required
@require_POST
def comment_create(request, slug):
    post = get_object_or_404(Post, slug=slug, is_public=True)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                actor=request.user,
                post=post,
                kind=Notification.Kind.COMMENT,
                message=f"{request.user.username} commented on your post.",
            )
        messages.success(request, "Comment added.")
    return redirect(post)


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post = comment.post
    if comment.author != request.user and post.author != request.user:
        return HttpResponseForbidden("Only the comment author or post author can delete this comment.")
    comment.delete()
    messages.success(request, "Comment deleted.")
    return redirect(post)


@login_required
def draft_list(request):
    drafts = (
        Post.objects.filter(author=request.user, is_public=False)
        .select_related("series")
        .prefetch_related("tags")
        .order_by("-updated_at")
    )
    return render(request, "blog/draft_list.html", {"drafts": drafts})


@login_required
def stats_dashboard(request):
    posts = (
        Post.objects.filter(author=request.user)
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
        )
        .order_by("-view_count", "-updated_at")
    )
    totals = {
        "posts": posts.count(),
        "views": sum(post.view_count for post in posts),
        "likes": sum(post.likes_count for post in posts),
        "comments": sum(post.comments_count for post in posts),
    }
    return render(
        request,
        "blog/stats_dashboard.html",
        {"posts": posts, "totals": totals},
    )
