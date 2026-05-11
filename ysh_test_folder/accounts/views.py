from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from blog.models import Post

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

    return render(
        request,
        "accounts/profile.html",
        {
            "owner": owner,
            "profile": profile_obj,
            "page_obj": page_obj,
        },
    )

# Create your views here.
