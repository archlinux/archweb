from django.contrib import admin

from .models import News


class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'postdate', 'last_modified', 'safe_mode')
    list_filter = ('postdate', 'author', 'safe_mode')
    search_fields = ('title', 'content')
    date_hierarchy = 'postdate'


admin.site.register(News, NewsAdmin)

# vim: set ts=4 sw=4 et:
