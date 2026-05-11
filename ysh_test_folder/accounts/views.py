from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from blog.models import Follow, Notification, Post

from .forms import SignUpForm
from .models import Profile


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "display_name": form.cleaned_data["display_name"],
                    "bio": form.cleaned_data["bio"],
                },
            )
            login(request, user)
            return redirect("profile", username=user.username)
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@require_POST
def local_login(request):
    user, created = User.objects.get_or_create(
        username="localtester",
        defaults={"email": "localtester@example.local"},
    )
    if created:
        user.set_password("local-password")
        user.save()
    Profile.objects.get_or_create(
        user=user,
        defaults={
            "display_name": "Local Tester",
            "bio": "Folder-local test account stored in this project's SQLite DB.",
        },
    )
    login(request, user)
    messages.success(request, "Logged in with the folder-local test account.")
    return redirect("post_list")


def profile(request, username):
    owner = get_object_or_404(User, username=username)
    profile_obj, _ = Profile.objects.get_or_create(user=owner)
    posts = (
        Post.objects.filter(author=owner, is_public=True)
        .select_related("author")
        .prefetch_related("tags", "likes")
        .order_by("-created_at")
    )
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    is_following = False
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=owner,
        ).exists()

    return render(
        request,
        "accounts/profile.html",
        {
            "owner": owner,
            "profile": profile_obj,
            "page_obj": page_obj,
            "is_following": is_following,
            "follower_count": owner.follower_links.count(),
            "following_count": owner.following_links.count(),
        },
    )


@login_required
@require_POST
def toggle_follow(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        messages.info(request, "You cannot follow yourself.")
        return redirect("profile", username=username)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target,
    )
    if created:
        Notification.objects.create(
            recipient=target,
            actor=request.user,
            kind=Notification.Kind.FOLLOW,
            message=f"{request.user.username} followed you.",
        )
        messages.success(request, f"Following {target.username}.")
    else:
        follow.delete()
        messages.success(request, f"Unfollowed {target.username}.")
    return redirect("profile", username=username)


@login_required
def notifications(request):
    items = list(request.user.notifications.select_related("actor", "post")[:50])
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, "accounts/notifications.html", {"notifications": items})
