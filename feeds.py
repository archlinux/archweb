from django.contrib.syndication.feeds import Feed
from archweb_dev.packages.models import Package
from archweb_dev.news.models import News
#from datetime import datetime

class PackageFeed(Feed):
    title       = 'Recent Package Updates'
    link       = '/packages/'
    description = 'Recent Package Updates'

    def items(self):
        return Package.objects.order_by('-last_update')[:10]

    def item_pubdate(self, item):
        return item.last_update

    def item_categories(self, item):
        return (item.repo.name,item.category.category)

class NewsFeed(Feed):
    title       = 'Recent News Updates'
    link       = '/news/'
    description = 'Recent News Updates'

    def items(self):
        return News.objects.order_by('-postdate', '-id')[:10]

    def item_pubdate(self, item):
        return item.postdate

    def item_author_name(self, item):
        return item.author.get_full_name()

# vim: set ts=4 sw=4 et:

