from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PostForm
from .models import Post, PostLike, Tag


def public_posts():
    return (
        Post.objects.filter(is_public=True)
        .select_related("author")
        .prefetch_related("tags", "likes")
        .order_by("-created_at")
    )


def paginate(request, queryset, per_page=10):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def post_list(request):
    return render(
        request,
        "blog/post_list.html",
        {
            "page_title": "최신 글",
            "page_obj": paginate(request, public_posts()),
            "tags": Tag.objects.all()[:20],
        },
    )


def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = public_posts().filter(tags=tag)
    return render(
        request,
        "blog/post_list.html",
        {
            "page_title": f"#{tag.name}",
            "page_obj": paginate(request, posts),
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
        raise Http404("글을 찾을 수 없습니다.")

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
            messages.success(request, "글을 발행했습니다.")
            return redirect(post)
    else:
        form = PostForm()

    return render(
        request,
        "blog/post_form.html",
        {"form": form, "page_title": "새 글 작성", "submit_label": "발행"},
    )


@login_required
def post_update(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.author != request.user:
        return HttpResponseForbidden("작성자만 수정할 수 있습니다.")

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            form.save_tags(post)
            messages.success(request, "글을 수정했습니다.")
            return redirect(post)
    else:
        form = PostForm(instance=post)

    return render(
        request,
        "blog/post_form.html",
        {"form": form, "post": post, "page_title": "글 수정", "submit_label": "저장"},
    )


@login_required
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.author != request.user:
        return HttpResponseForbidden("작성자만 삭제할 수 있습니다.")

    if request.method == "POST":
        post.delete()
        messages.success(request, "글을 삭제했습니다.")
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

# Create your views here.
