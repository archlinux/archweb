from django.db import models
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from main.utils import parse_markdown


class News(models.Model):
    slug = models.SlugField(max_length=255, unique=True)
    author = models.ForeignKey(User, related_name='news_author',
            on_delete=models.PROTECT)
    postdate = models.DateTimeField("post date", db_index=True)
    last_modified = models.DateTimeField(editable=False, db_index=True)
    title = models.CharField(max_length=255)
    guid = models.CharField(max_length=255, editable=False)
    content = models.TextField()
    safe_mode = models.BooleanField(default=True)
    send_announce = models.BooleanField(default=True)

    def get_absolute_url(self):
        return '/news/%s/' % self.slug

    def html(self):
        return mark_safe(parse_markdown(self.content, not self.safe_mode))

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'news'
        verbose_name_plural = 'news'
        get_latest_by = 'postdate'
        ordering = ('-postdate',)


def set_news_fields(sender, **kwargs):
    news = kwargs['instance']
    current_time = now()
    news.last_modified = current_time
    if not news.postdate:
        news.postdate = current_time
        # http://diveintomark.org/archives/2004/05/28/howto-atom-id
        news.guid = 'tag:%s,%s:%s' % (Site.objects.get_current(),
                current_time.strftime('%Y-%m-%d'), news.get_absolute_url())


from django.db.models.signals import pre_save

pre_save.connect(set_news_fields, sender=News,
        dispatch_uid="news.models")

# vim: set ts=4 sw=4 et:
