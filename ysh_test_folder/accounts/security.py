from django.core.cache import cache


LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "::1", "[::1]"}


def request_hostname(request):
    host = request.get_host().split(":", 1)[0].lower()
    return host.strip("[]")


def is_local_request(request):
    return request_hostname(request) in {"localhost", "127.0.0.1", "::1"}


def client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def is_rate_limited(request, scope, limit=20, window_seconds=60, identifier=None):
    identity = identifier or client_ip(request)
    key = f"rl:{scope}:{identity}"
    current = cache.get(key, 0)
    if current >= limit:
        return True
    if current == 0:
        cache.set(key, 1, window_seconds)
    else:
        cache.incr(key)
    return False
