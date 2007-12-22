from django.core import validators
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from string import *
import sgmllib

#from archweb_dev.packages.models import Maintainer
#from archweb_dev.settings import BADPRIVS_URL
#def is_maintainer(view_func, badprivs_url=BADPRIVS_URL):
#	"""
#	Decorator for views that checks that the logged-in user has a corresponding
#	record in the Maintainers table.  If not, the user is forwarded to a
#	"bad-privileges" page.
#	"""
#	def _dec(view_func):
#		def _checkuser(request, *args, **kwargs):
#			try:
#				m = Maintainer.objects.get(username=request.user.username)
#			except Maintainer.DoesNotExist:
#				return HttpResponseRedirect(badprivs_url)
#			return view_func(request, *args, **kwargs)
#
#		return _checkuser
#	return _dec(view_func)

def render_template(template, request, context=None):
	"""
	A shortcut to render_to_response with a RequestContext.  Also includes
	request.path in the context, so both 'path' and 'user' are accessible to
	the template.
	"""
	if context:
		context['path'] = request.path
		return render_to_response(template, context_instance=RequestContext(request, context))
	else:
		return render_to_response(template, context_instance=RequestContext(request))

def validate(errdict, fieldname, fieldval, validator, blankallowed, request):
	"""
	A helper function that allows easy access to Django's validators without
	going through a Manipulator object.  Will return a dict of all triggered
	errors.
	"""
	if blankallowed and not fieldval:
		return
	alldata = ' '.join(request.POST.values()) + ' '.join(request.GET.values())
	try:
		validator(fieldval, alldata)
	except validators.ValidationError, e:
		if not errdict.has_key(fieldname): errdict[fieldname] = []
		errdict[fieldname].append(e)


# XXX: unused right now, probably not needed
class Stripper(sgmllib.SGMLParser):
	"""Helper class to strip HTML tags"""
	def __init__(self):
		sgmllib.SGMLParser.__init__(self)

	def strip(self, some_html):
		"""Strips all HTML tags and leading/trailing whitespace"""
		self.theString = ""
		self.feed(some_html)
		self.close()
		return self.theString

	def handle_data(self, data):
		self.theString += data
