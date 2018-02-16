from datetime import datetime, timedelta
from pytz import utc

from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from main.models import Package
from news.models import News
from packages.utils import get_group_info, get_split_packages_info
from releng.models import Release
from todolists.models import Todolist


class PackagesSitemap(Sitemap):
    def items(self):
        return Package.objects.normal().only(
                'pkgname', 'last_update', 'files_last_update',
                'repo__name', 'repo__testing', 'repo__staging',
                'arch__name')

    def lastmod(self, obj):
        return obj.last_update

    def changefreq(self, obj):
        if obj.repo.testing or obj.repo.staging:
            return "daily"
        return "weekly"

    def priority(self, obj):
        if obj.repo.testing:
            return "0.4"
        if obj.repo.staging:
            return "0.1"
        return "0.5"


class PackageFilesSitemap(PackagesSitemap):
    changefreq = "weekly"
    priority = "0.1"

    def location(self, obj):
        return PackagesSitemap.location(self, obj) + 'files/'

    def lastmod(self, obj):
        return obj.files_last_update


class PackageGroupsSitemap(Sitemap):
    changefreq = "weekly"
    priority = "0.4"

    def items(self):
        return get_group_info()

    def lastmod(self, obj):
        return obj['last_update']

    def location(self, obj):
        return '/groups/%s/%s/' % (obj['arch'], obj['name'])


class SplitPackagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = "0.3"

    def items(self):
        return get_split_packages_info()

    def lastmod(self, obj):
        return obj['last_update']

    def location(self, obj):
        return '/packages/%s/%s/%s/' % (
                obj['repo'].name.lower(), obj['arch'], obj['pkgbase'])


class NewsSitemap(Sitemap):
    def __init__(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        self.one_day_ago = now - timedelta(days=1)
        self.one_week_ago = now - timedelta(days=7)

    def items(self):
        return News.objects.all().defer('content', 'guid', 'title')

    def lastmod(self, obj):
        return obj.last_modified

    def priority(self, obj):
        if obj.last_modified > self.one_week_ago:
            return "0.9"
        return "0.8"

    def changefreq(self, obj):
        if obj.last_modified > self.one_day_ago:
            return 'daily'
        if obj.last_modified > self.one_week_ago:
            return 'weekly'
        return 'yearly'


class RecentNewsSitemap(NewsSitemap):
    def items(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        cutoff = now - timedelta(days=30)
        return list(super(RecentNewsSitemap, self).items()).filter(postdate__gte=cutoff)


class ReleasesSitemap(Sitemap):
    changefreq = "monthly"

    def items(self):
        return Release.objects.all().defer('info', 'torrent_data')

    def lastmod(self, obj):
        return obj.last_modified

    def priority(self, obj):
        if obj.available:
            return "0.6"
        return "0.2"


class TodolistSitemap(Sitemap):
    priority = "0.4"

    def __init__(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        self.two_weeks_ago = now - timedelta(days=14)

    def items(self):
        return Todolist.objects.all().defer('raw').order_by('created')

    def lastmod(self, obj):
        return obj.last_modified

    def changefreq(self, obj):
        if obj.last_modified > self.two_weeks_ago:
            return 'weekly'
        return 'monthly'


class BaseSitemap(Sitemap):
    DEFAULT_PRIORITY = 0.7

    base_viewnames = (
            ('index', 1.0, 'hourly'),
            ('packages-search', 0.8, 'hourly'),
            ('page-download', 0.8, 'monthly'),
            ('page-keys', 0.8, 'weekly'),
            ('news-list', 0.7, 'weekly'),
            ('groups-list', 0.5, 'weekly'),
            ('mirror-status', 0.4, 'hourly'),
            'page-about',
            'page-art',
            'page-svn',
            'page-donate',
            'feeds-list',
            'mirror-list',
            'mirror-status',
            'mirrorlist',
            'packages-differences',
            'releng-release-list',
            'visualize-index',
    )

    def items(self):
        return self.base_viewnames

    def location(self, obj):
        name = obj
        if isinstance(obj, tuple):
            name = obj[0]
        return reverse(name)

    def priority(self, obj):
        if isinstance(obj, tuple):
            return obj[1]
        return self.DEFAULT_PRIORITY

    def changefreq(self, obj):
        if isinstance(obj, tuple):
            return obj[2]
        return 'monthly'

# vim: set ts=4 sw=4 et:
