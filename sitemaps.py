from django.contrib.sitemaps import Sitemap
from main.models import Package, News
from packages.views import get_group_info

class PackagesSitemap(Sitemap):
    changefreq = "weekly"
    priority = "0.5"

    def items(self):
        return Package.objects.select_related('arch', 'repo').all()
        return Package.objects.all()

    def lastmod(self, obj):
        return obj.last_update


class PackageFilesSitemap(PackagesSitemap):
    changefreq = "monthly"
    priority = "0.3"

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


class NewsSitemap(Sitemap):
    changefreq = "never"
    priority = "0.7"

    def items(self):
        return News.objects.all()

    def lastmod(self, obj):
        return obj.postdate

# vim: set ts=4 sw=4 et:
