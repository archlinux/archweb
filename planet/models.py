from django.db import models


# FeedItem summary field length
FEEDITEM_SUMMARY_LIMIT = 2048


class Feed(models.Model):
    title = models.CharField(max_length=255)
    website = models.CharField(max_length=200, null=True, blank=True)
    website_rss = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'feeds'
        verbose_name_plural = 'feeds'
        get_latest_by = 'title'
        ordering = ('-title',)


class FeedItem(models.Model):
    title = models.CharField(max_length=255)
    summary = models.CharField(max_length=FEEDITEM_SUMMARY_LIMIT)
    feed = models.ForeignKey(Feed, related_name='items',
                             on_delete=models.CASCADE, null=True)
    author = models.CharField(max_length=255)
    publishdate = models.DateTimeField("publish date", db_index=True)
    url = models.CharField('URL', max_length=255)

    def get_absolute_url(self):
        return self.url

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'feeditems'
        verbose_name_plural = 'Feed Items'
        get_latest_by = 'publishdate'
        ordering = ('-publishdate',)


class Planet(models.Model):
    '''
    The planet model contains related Arch Linux planet instances.
    '''

    name = models.CharField(max_length=255)
    website = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'planets'
        verbose_name_plural = 'Worldwide Planets'
        get_latest_by = 'name'
        ordering = ('-name',)

# vim: set ts=4 sw=4 et:
