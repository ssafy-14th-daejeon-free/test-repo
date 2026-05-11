from django.conf import settings


def local_counts(request):
    context = {"enable_local_login": settings.ENABLE_LOCAL_LOGIN}
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return context

    context.update({
        "unread_notification_count": user.notifications.filter(
            is_read=False
        ).count(),
        "draft_count": user.posts.filter(is_public=False).count(),
    })
    return context
