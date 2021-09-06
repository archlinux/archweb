from django.contrib import admin

from planet.models import Feed, FeedItem, Planet


class FeedItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'publishdate',)
    list_filter = ('publishdate',)
    search_fields = ('title',)


class FeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'website',)
    list_filter = ('title',)
    search_fields = ('title',)


class PlanetAdmin(admin.ModelAdmin):
    list_display = ('name', 'website',)
    list_filter = ('name',)
    search_fields = ('name',)


admin.site.register(Feed, FeedAdmin)
admin.site.register(FeedItem, FeedItemAdmin)
admin.site.register(Planet, PlanetAdmin)

# vim: set ts=4 sw=4 et:
