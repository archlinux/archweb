from django.shortcuts import render
from django.views.decorators.cache import cache_control

from planet.models import Feed, FeedItem, Planet


@cache_control(max_age=307)
def index(request):
    context = {
        'official_feeds': Feed.objects.all(),
        'planets': Planet.objects.all(),
        'feed_items': FeedItem.objects.order_by('-publishdate')[:25],
    }
    return render(request, 'planet/index.html', context)
