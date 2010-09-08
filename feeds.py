import datetime

from django.contrib.syndication.views import Feed
from django.db.models import Q

from main.models import Arch, Repo, Package
from news.models import News

class PackageFeed(Feed):
    link = '/packages/'
    title_template = 'feeds/packages_title.html'
    description_template = 'feeds/packages_description.html'

    def get_object(self, request, arch='', repo=''):
        obj = dict()
        qs = Package.objects.select_related('arch', 'repo').order_by('-last_update')

        if arch != '':
            # feed for a single arch, also include 'any' packages everywhere
            a = Arch.objects.get(name=arch)
            qs = qs.filter(Q(arch=a) | Q(arch__agnostic=True))
            obj['arch'] = a
        if repo != '':
            # feed for a single arch AND repo
            r = Repo.objects.get(name=repo)
            qs = qs.filter(repo=r)
            obj['repo'] = r
        obj['qs'] = qs[:50]
        return obj

    def title(self, obj):
        s = 'Arch Linux: Recent package updates'
        if 'repo' in obj:
            s += ' (%s [%s])' % (obj['arch'].name, obj['repo'].name.lower())
        elif 'arch' in obj:
            s += ' (%s)' % (obj['arch'].name)
        return s

    def description(self, obj):
        s = 'Recently updated packages in the Arch Linux package repositories'
        if 'arch' in obj:
            s += ' for the \'%s\' architecture' % obj['arch'].name.lower()
            if not obj['arch'].agnostic:
                s += ' (including \'any\' packages)'
        if 'repo' in obj:
            s += ' in the [%s] repository' % obj['repo'].name.lower()
        s += '.'
        return s

    def items(self, obj):
        return obj['qs']

    def item_pubdate(self, item):
        return item.last_update

    def item_categories(self, item):
        return (item.repo.name, item.arch.name)


class NewsFeed(Feed):
    title = 'Arch Linux: Recent news updates'
    link = '/news/'
    description = 'The latest and greatest news from the Arch Linux distribution.'
    title_template = 'feeds/news_title.html'
    description_template = 'feeds/news_description.html'

    def items(self):
        return News.objects.select_related('author').order_by('-postdate', '-id')[:10]

    def item_pubdate(self, item):
        d = item.postdate
        return datetime.datetime(d.year, d.month, d.day)

    def item_author_name(self, item):
        return item.author.get_full_name()

# vim: set ts=4 sw=4 et:
