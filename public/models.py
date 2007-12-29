from django.db import models
from django.contrib.auth.models import User

class Mirror(models.Model):
    id = models.AutoField(primary_key=True)
    domain = models.CharField(maxlength=255)
    country = models.CharField(maxlength=255)
    url = models.CharField(maxlength=255)
    protocol_list = models.CharField(maxlength=255, null=True, blank=True)
    admin_email = models.CharField(maxlength=255, null=True, blank=True)
    def __str__(self):
        return self.domain
    class Admin:
        list_display = ('domain', 'country')
        list_filter = ('country',)
        ordering = ['domain']
        search_fields = ('domain')
        pass

class Donator(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(maxlength=255)
    def __str__(self):
        return self.name
    class Admin:
        ordering = ['name']
        search_fields = ('name')
        pass

class UserProfile(models.Model):
    id = models.AutoField(primary_key=True) # not technically needed
    notify = models.BooleanField("Send notifications", default=True, help_text="When enabled, user will recieve 'flag out of date' notifications")
    alias = models.CharField(core=True, maxlength=50, help_text="Required field")
    public_email = models.CharField(core=True, maxlength=50, help_text="Required field")
    other_contact = models.CharField(maxlength=100, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    yob = models.IntegerField(null=True, blank=True)
    location = models.CharField(maxlength=50, null=True, blank=True)
    languages = models.CharField(maxlength=50, null=True, blank=True)
    interests = models.CharField(maxlength=255, null=True, blank=True)
    occupation = models.CharField(maxlength=50, null=True, blank=True)
    roles = models.CharField(maxlength=255, null=True, blank=True)
    favorite_distros = models.CharField(maxlength=255, null=True, blank=True)
    picture = models.FileField(upload_to='devs', default='devs/silhouette.png')
    user = models.ForeignKey(User, edit_inline=models.STACKED, num_in_admin=1, min_num_in_admin=1, max_num_in_admin=1, num_extra_on_change=0, unique=True)
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Additional Profile Data'
        verbose_name_plural = 'Additional Profile Data'

