import django.newforms as forms

from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from archweb_dev.main.utils import render_response
from archweb_dev.main.models import Todolist, TodolistPkg, Package
from archweb_dev.main.models import Arch, Repo

# FIXME: ugly hackery. http://code.djangoproject.com/ticket/3450
import django.db
IntegrityError = django.db.backend.Database.IntegrityError

class TodoListForm(forms.Form):
    name = forms.CharField(max_length=255,
            widget=forms.TextInput(attrs={'size': '30'}))
    description = forms.CharField(required=False,
            widget=forms.Textarea(attrs={'rows': '4', 'cols': '60'}))
    packages = forms.CharField(required=False,
            help_text='(one per line)',
            widget=forms.Textarea(attrs={'rows': '20', 'cols': '60'}))

    def clean_packages(self):
        packages = []
        for p in self.clean_data['packages'].split("\n"):
            for pkg in Package.objects.filter(
                    pkgname=p.strip()).order_by('arch').distinct():
                packages .append(pkg)

        return packages


def flag(request, listid, pkgid):
    list = get_object_or_404(Todolist, id=listid)
    pkg  = get_object_or_404(TodolistPkg, id=pkgid)
    pkg.complete = not pkg.complete
    pkg.save()
    return HttpResponseRedirect('/todo/%s/' % (listid))

def view(request, listid):
    list = get_object_or_404(Todolist, id=listid)
    pkgs = TodolistPkg.objects.filter(list=list.id).order_by('pkg')
    return render_response(
        request, 
        'todolists/view.html', 
        {'list':list,'pkgs':pkgs})

def list(request):
    lists = Todolist.objects.order_by('-date_added')
    for l in lists:
        l.complete = TodolistPkg.objects.filter(
            list=l.id,complete=False).count() == 0
    return render_response(request, 'todolists/list.html', {'lists':lists})

@permission_required('todolists.add_todolist')
def add(request):
    if request.POST:
        # create the list
        form = TodoListForm(request.POST)
        if form.is_valid():
            todo = Todolist(
                creator     = request.user,
                name        = form.clean_data['name'],
                description = form.clean_data['description'])
            todo.save()
            # now link in packages
            for pkg in form.clean_data['packages']:
                todopkg = TodolistPkg(list = todo, pkg = pkg)
                todopkg.save()
            return HttpResponseRedirect('/todo/')
    else:
        form = TodoListForm()

    page_dict = {
            'title': 'Add To-do List',
            'form': form,
            'submit_text': 'Create List'
            }
    return render_response(request, 'general_form.html', page_dict)

# vim: set ts=4 sw=4 et:

