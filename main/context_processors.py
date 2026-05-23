from django.conf import settings
from django.http import HttpRequest


def mastodon_link(request: HttpRequest) -> dict[str, str]:
    return {'MASTODON_LINK': getattr(settings, "MASTODON_LINK", "")}
