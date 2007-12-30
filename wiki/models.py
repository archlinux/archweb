from django.db import models
from django.contrib.auth.models import User

class Wikipage(models.Model):
    """Wiki page storage"""
    title = models.CharField(maxlength=255)
    content = models.TextField()
    last_author = models.ForeignKey(User)
    class Meta:
        db_table = 'wikipages'

    def editurl(self):
        return "/wiki/edit/" + self.title + "/"

    def __repr__(self):
        return self.title

# vim: set ts=4 sw=4 et:

