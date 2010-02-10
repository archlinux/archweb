from django.contrib.sitemaps import Sitemap
from main.models import Package, News

class PackagesSitemap(Sitemap):
    changefreq = "monthly"
    priority = "0.4"

    def items(self):
        return Package.objects.select_related('arch', 'repo').all()
        return Package.objects.all()

    def lastmod(self, obj):
        return obj.last_update

class NewsSitemap(Sitemap):
    changefreq = "never"
    priority = "0.7"

    def items(self):
        return News.objects.all()

    def lastmod(self, obj):
        return obj.postdate

# vim: set ts=4 sw=4 et:

