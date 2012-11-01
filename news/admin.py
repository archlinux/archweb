from django.contrib import admin

from .models import News

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'postdate', 'last_modified', 'safe_mode')
    list_filter = ('postdate', 'author')
    search_fields = ('title', 'content')

admin.site.register(News, NewsAdmin)
