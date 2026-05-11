from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/local-login/", views.local_login, name="local_login"),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("notifications/", views.notifications, name="notifications"),
    path("@<str:username>/follow/", views.toggle_follow, name="toggle_follow"),
    path("@<str:username>/", views.profile, name="profile"),
]
