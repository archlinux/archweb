from django.contrib import admin

from .models import News

class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'postdate')
    list_filter = ('author', 'postdate')
    search_fields = ('title', 'content')

admin.site.register(News, NewsAdmin)
