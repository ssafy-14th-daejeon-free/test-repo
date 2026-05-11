def local_counts(request):
    if not request.user.is_authenticated:
        return {}

    return {
        "unread_notification_count": request.user.notifications.filter(
            is_read=False
        ).count(),
        "draft_count": request.user.posts.filter(is_public=False).count(),
    }
