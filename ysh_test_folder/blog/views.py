from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PostForm
from .models import Post, PostLike, Tag


FEED_TABS = [
    ("trending", "Trending"),
    ("recommended", "Recommended"),
    ("latest", "Latest"),
    ("feed", "Feed"),
]


def public_posts():
    return (
        Post.objects.filter(is_public=True)
        .select_related("author")
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
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(tags__name__icontains=search_query)
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


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related("author").prefetch_related("tags", "likes"),
        slug=slug,
    )
    if not post.is_public and post.author != request.user:
        raise Http404("Post not found.")

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
        },
    )


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_tags(post)
            messages.success(request, "Post published.")
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
            post = form.save()
            form.save_tags(post)
            messages.success(request, "Post updated.")
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
    if not created:
        like.delete()
    return redirect(post)
