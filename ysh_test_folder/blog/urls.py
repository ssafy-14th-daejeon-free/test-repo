from django.urls import path

from . import views

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("me/drafts/", views.draft_list, name="draft_list"),
    path("me/stats/", views.stats_dashboard, name="stats_dashboard"),
    path("posts/new/", views.post_create, name="post_create"),
    path("posts/<str:slug>/", views.post_detail, name="post_detail"),
    path("posts/<str:slug>/edit/", views.post_update, name="post_update"),
    path("posts/<str:slug>/delete/", views.post_delete, name="post_delete"),
    path("posts/<str:slug>/like/", views.toggle_like, name="post_like"),
    path("posts/<str:slug>/comments/", views.comment_create, name="comment_create"),
    path("comments/<int:pk>/delete/", views.comment_delete, name="comment_delete"),
    path("series/<str:slug>/", views.series_posts, name="series_posts"),
    path("tags/<str:slug>/", views.tag_posts, name="tag_posts"),
]
