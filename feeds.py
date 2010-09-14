import datetime

from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.utils.hashcompat import md5_constructor
from django.views.decorators.http import condition

from main.models import Arch, Repo, Package
from news.models import News

def package_etag(request, *args, **kwargs):
    latest = Package.objects.latest('last_update')
    if latest:
        return md5_constructor(
                str(kwargs) + str(latest.last_update)).hexdigest()
    return None

def package_last_modified(request, *args, **kwargs):
    # we could break this down based on the request url, but it would probably
    # cost us more in query time to do so.
    latest = Package.objects.latest('last_update')
    if latest:
        return latest.last_update
    return None

class PackageFeed(Feed):
    link = '/packages/'
    title_template = 'feeds/packages_title.html'
    description_template = 'feeds/packages_description.html'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(etag_func=package_etag, last_modified_func=package_last_modified)
        return wrapper(super(PackageFeed, self).__call__)(request, *args, **kwargs)

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


def news_etag(request, *args, **kwargs):
    latest = News.objects.latest('last_modified')
    if latest:
        return md5_constructor(str(latest.last_modified)).hexdigest()
    return None

def news_last_modified(request):
    latest = News.objects.latest('last_modified')
    if latest:
        return latest.last_modified
    return None

class NewsFeed(Feed):
    title = 'Arch Linux: Recent news updates'
    link = '/news/'
    description = 'The latest and greatest news from the Arch Linux distribution.'
    title_template = 'feeds/news_title.html'
    description_template = 'feeds/news_description.html'

    def __call__(self, request, *args, **kwargs):
        wrapper = condition(etag_func=news_etag, last_modified_func=news_last_modified)
        return wrapper(super(NewsFeed, self).__call__)(request, *args, **kwargs)

    def items(self):
        return News.objects.select_related('author').order_by('-postdate', '-id')[:10]

    def item_pubdate(self, item):
        d = item.postdate
        return datetime.datetime(d.year, d.month, d.day)

    def item_author_name(self, item):
        return item.author.get_full_name()

# vim: set ts=4 sw=4 et:
