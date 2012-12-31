from django.contrib import admin

from .models import Todolist


class TodolistAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'created', 'description')
    list_filter = ('created', 'creator')
    search_fields = ('name', 'description')
    date_hierarchy = 'created'


admin.site.register(Todolist, TodolistAdmin)

# vim: set ts=4 sw=4 et:
