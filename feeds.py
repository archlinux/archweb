import datetime
from django.contrib.syndication.feeds import Feed
from archweb.main.models import Package, News
#from datetime import datetime

class PackageFeed(Feed):
    title       = 'Recent Package Updates'
    link       = '/packages/'
    description = 'Recent Package Updates'

    def items(self):
        return Package.objects.order_by('-last_update')[:24]

    def item_pubdate(self, item):
        return item.last_update

    def item_categories(self, item):
        return (item.repo.name,item.arch.name)

class NewsFeed(Feed):
    title       = 'Recent News Updates'
    link       = '/news/'
    description = 'Recent News Updates'

    def items(self):
        return News.objects.order_by('-postdate', '-id')[:10]

    def item_pubdate(self, item):
        d = item.postdate
        return datetime.datetime(d.year, d.month, d.day)

    def item_author_name(self, item):
        return item.author.get_full_name()

# vim: set ts=4 sw=4 et:

