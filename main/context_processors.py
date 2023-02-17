from django.conf import settings


def mastodon_link(request):
    return {'MASTODON_LINK': getattr(settings, "MASTODON_LINK", "")}
