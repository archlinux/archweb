#
# Based on code from http://e-scribe.com/news/210
#
from django.http import HttpResponse, HttpResponseRedirect
from archweb_dev.main.utils import render_response
from archweb_dev.main.models import Wikipage

def index(request):
    """Return a list of all wiki pages"""
    pages = Wikipage.objects.all().order_by('title')
    return render_response(request, 'wiki/home.html', {'pages':pages})

def main(request):
    """Return the Index wiki page"""
    return HttpResponseRedirect("/wiki/WikiIndex/")

def page(request, title):
    """Display page, or redirect to root if page doesn't exist yet"""
    try:
        page = Wikipage.objects.get(title__exact=title)
        return render_response(request, 'wiki/page.html', {'page':page})
    except Wikipage.DoesNotExist:
        return HttpResponseRedirect("/wiki/edit/%s/" % title)

def edit(request, title):
    """Process submitted page edits (POST) or display editing form (GET)"""
    if request.POST:
        try:
            page = Wikipage.objects.get(title__exact=title)
        except Wikipage.DoesNotExist:
            # Must be a new one; let's create it
            page = Wikipage(title=title)
        page.content = request.POST['content']
        page.title = request.POST['title']
        page.last_author = request.user
        page.save()
        return HttpResponseRedirect("/wiki/" + page.title + "/")
    else:
        try:
            page = Wikipage.objects.get(title__exact=title)
        except Wikipage.DoesNotExist:
            # create a dummy page object -- note that it is not saved!
            page = Wikipage(title=title)
            page.body = "<!-- Enter content here -->"
        return render_response(request, 'wiki/edit.html', {'page':page})

def delete(request):
    """Delete a page"""
    if request.POST:
        title = request.POST['title']
        try:
            page = Wikipage.objects.get(title__exact=title)
        except Wikipage.DoesNotExist:
            return HttpResponseRedirect("/wiki/")
        page.delete()
    return HttpResponseRedirect("/wiki/")

# vim: set ts=4 sw=4 et:

