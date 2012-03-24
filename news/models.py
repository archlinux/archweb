from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from main.utils import utc_now


class News(models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    author = models.ForeignKey(User, related_name='news_author',
            on_delete=models.PROTECT)
    postdate = models.DateTimeField("post date", db_index=True)
    last_modified = models.DateTimeField(editable=False, db_index=True)
    title = models.CharField(max_length=255)
    guid = models.CharField(max_length=255, editable=False)
    content = models.TextField()

    def get_absolute_url(self):
        return '/news/%s/' % self.slug

    def __unicode__(self):
        return self.title

    class Meta:
        db_table = 'news'
        verbose_name_plural = 'news'
        get_latest_by = 'postdate'
        ordering = ['-postdate']

def set_news_fields(sender, **kwargs):
    news = kwargs['instance']
    now = utc_now()
    news.last_modified = now
    if not news.postdate:
        news.postdate = now
        # http://diveintomark.org/archives/2004/05/28/howto-atom-id
        news.guid = 'tag:%s,%s:%s' % (Site.objects.get_current(),
                now.strftime('%Y-%m-%d'), news.get_absolute_url())

# connect signals needed to keep cache in line with reality
from main.utils import refresh_latest
from django.db.models.signals import pre_save, post_save

post_save.connect(refresh_latest, sender=News,
        dispatch_uid="news.models")
pre_save.connect(set_news_fields, sender=News,
        dispatch_uid="news.models")

# vim: set ts=4 sw=4 et:
