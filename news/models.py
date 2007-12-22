from django.db import models
from django.contrib.auth.models import User
import re
from archweb_dev.utils import Stripper

class News(models.Model):
	id = models.AutoField(primary_key=True)
	author = models.ForeignKey(User)
	postdate = models.DateField(auto_now_add=True)
	title = models.CharField(maxlength=255)
	content = models.TextField()
	class Meta:
		db_table = 'news'
		verbose_name_plural = 'news'
		get_latest_by = 'postdate'
		ordering = ['-postdate', '-id']

	def get_absolute_url(self):
		return '/news/%i/' % self.id
