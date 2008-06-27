import django.newforms as forms

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from archweb_dev.main.utils import render_response
from archweb_dev.main.models import Todolist, TodolistPkg, Package
from archweb_dev.main.models import Arch, Repo

# FIXME: ugly hackery. http://code.djangoproject.com/ticket/3450
import django.db
IntegrityError = django.db.backend.Database.IntegrityError

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
        try:
            m = User.objects.get(username=request.user.username)
        except User.DoesNotExist:
            return render_response(request, 'error_page.html',
                {'errmsg': 'Cannot find a maintainer record for you!'})
        # create the list
        todo = Todolist(
            creator     = m,
            name        = request.POST.get('name'),
            description = request.POST.get('description'))
        todo.save()
        # now link in packages
        for p in request.POST.get('packages').split("\n"):
            for pkg in Package.objects.filter(
                    pkgname=p.strip()).order_by('arch'):
                todopkg = TodolistPkg(
                    list = todo,
                    pkg  = pkg)
                try:
                    todopkg.save()
                except IntegrityError, (num, desc):
                    if num != 1062: # duplicate entry aka dupe package on list
                        raise
        return HttpResponseRedirect('/todo/')
    return render_response(request, 'todolists/add.html')

# vim: set ts=4 sw=4 et:

