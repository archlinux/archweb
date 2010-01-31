import datetime
from django.contrib.syndication.feeds import Feed
from archweb.main.models import Package, News

class PackageFeed(Feed):
    title       = 'Arch Linux Recent Package Updates'
    link       = '/packages/'
    description = 'Recently updated packages in the Arch Linux package repositories.'

    def items(self):
        return Package.objects.select_related('arch', 'repo').order_by('-last_update')[:24]

    def item_pubdate(self, item):
        return item.last_update

    def item_categories(self, item):
        return (item.repo.name,item.arch.name)

class NewsFeed(Feed):
    title       = 'Arch Linux Recent News Updates'
    link       = '/news/'
    description = 'The latest and greatest news from the Arch Linux distribution.'

    def items(self):
        return News.objects.select_related('author').order_by('-postdate', '-id')[:10]

    def item_pubdate(self, item):
        d = item.postdate
        return datetime.datetime(d.year, d.month, d.day)

    def item_author_name(self, item):
        return item.author.get_full_name()

# vim: set ts=4 sw=4 et:

