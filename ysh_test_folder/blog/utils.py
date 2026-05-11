from urllib.parse import urlparse

import bleach
import markdown
from django.conf import settings


ALLOWED_TAGS = {
    "a",
    "abbr",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "ul",
}

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "abbr": ["title"],
}


def render_markdown(value):
    raw_html = markdown.markdown(
        value or "",
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html",
    )
    return bleach.clean(
        raw_html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )


def is_allowed_cover_url(value):
    if not value:
        return True
    parsed = urlparse(value)
    return (
        parsed.scheme in {"http", "https"}
        and parsed.hostname is not None
        and parsed.hostname.lower() in settings.ALLOWED_COVER_IMAGE_HOSTS
    )
