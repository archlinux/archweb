from django import forms

from django.http import HttpResponse
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count
from django.views.decorators.cache import never_cache
from django.views.generic.create_update import delete_object
from django.views.generic.simple import direct_to_template
from django.template import Context, loader
from django.utils import simplejson

from main.models import Todolist, TodolistPkg, Package

class TodoListForm(forms.Form):
    name = forms.CharField(max_length=255,
            widget=forms.TextInput(attrs={'size': '30'}))
    description = forms.CharField(required=False,
            widget=forms.Textarea(attrs={'rows': '4', 'cols': '60'}))
    packages = forms.CharField(required=False,
            help_text='(one per line)',
            widget=forms.Textarea(attrs={'rows': '20', 'cols': '60'}))

    def clean_packages(self):
        package_names = [s.strip() for s in
                self.cleaned_data['packages'].split("\n")]
        package_names = set(package_names)
        packages = Package.objects.filter(
                pkgname__in=package_names).exclude(
                repo__testing=True).order_by('arch')
        return packages


@login_required
@never_cache
def flag(request, listid, pkgid):
    list = get_object_or_404(Todolist, id=listid)
    pkg  = get_object_or_404(TodolistPkg, id=pkgid)
    pkg.complete = not pkg.complete
    pkg.save()
    if request.is_ajax():
        return HttpResponse(
            simplejson.dumps({'complete': pkg.complete}),
            mimetype='application/json')
    return redirect(list)

@login_required
@never_cache
def view(request, listid):
    list = get_object_or_404(Todolist, id=listid)
    return direct_to_template(request, 'todolists/view.html', {'list': list})

@login_required
@never_cache
def list(request):
    lists = Todolist.objects.select_related('creator').annotate(
            pkg_count=Count('todolistpkg')).order_by('-date_added')
    incomplete = Todolist.objects.filter(todolistpkg__complete=False).annotate(
            Count('todolistpkg')).values_list('id', 'todolistpkg__count')

    # tag each list with an incomplete package count
    lookup = {}
    for k, v in incomplete:
        lookup[k] = v
    for l in lists:
        l.incomplete_count = lookup.get(l.id, 0)

    return direct_to_template(request, 'todolists/list.html', {'lists': lists})

# TODO: this calls for transaction management and async emailing
@permission_required('main.add_todolist')
@never_cache
def add(request):
    if request.POST:
        form = TodoListForm(request.POST)
        if form.is_valid():
            todo = Todolist.objects.create(
                creator     = request.user,
                name        = form.cleaned_data['name'],
                description = form.cleaned_data['description'])

            for pkg in form.cleaned_data['packages']:
                tpkg = TodolistPkg.objects.create(list=todo, pkg=pkg)
                send_todolist_email(tpkg)

            return redirect('/todo/')
    else:
        form = TodoListForm()

    page_dict = {
            'title': 'Add Todo List',
            'form': form,
            'submit_text': 'Create List'
    }
    return direct_to_template(request, 'general_form.html', page_dict)

# TODO: this calls for transaction management and async emailing
@permission_required('main.change_todolist')
@never_cache
def edit(request, list_id):
    todo_list = get_object_or_404(Todolist, id=list_id)
    if request.POST:
        form = TodoListForm(request.POST)
        if form.is_valid():
            todo_list.name = form.cleaned_data['name']
            todo_list.description = form.cleaned_data['description']
            todo_list.save()

            packages = [p.pkg for p in todo_list.packages]

            # first delete any packages not in the new list
            for p in todo_list.packages:
                if p.pkg not in form.cleaned_data['packages']:
                    p.delete()

            # now add any packages not in the old list
            for pkg in form.cleaned_data['packages']:
                if pkg not in packages:
                    tpkg = TodolistPkg.objects.create(
                            list=todo_list, pkg=pkg)
                    send_todolist_email(tpkg)

            return redirect(todo_list)
    else:
        form = TodoListForm(initial={
            'name': todo_list.name,
            'description': todo_list.description,
            'packages': '\n'.join(todo_list.package_names),
        })
    page_dict = {
            'title': 'Edit Todo List: %s' % todo_list.name,
            'form': form,
            'submit_text': 'Save List'
    }
    return direct_to_template(request, 'general_form.html', page_dict)

@permission_required('main.delete_todolist')
@never_cache
def delete_todolist(request, object_id):
    return delete_object(request, object_id=object_id, model=Todolist,
            template_name="todolists/todolist_confirm_delete.html",
            post_delete_redirect='/todo/')

def send_todolist_email(todo):
    '''Sends an e-mail to the maintainer of a package notifying them that the
    package has been added to a todo list'''
    maints = todo.pkg.maintainers
    if not maints:
        return

    page_dict = {
            'pkg': todo.pkg,
            'todolist': todo.list,
            'weburl': todo.pkg.get_full_url()
    }
    t = loader.get_template('todolists/email_notification.txt')
    c = Context(page_dict)
    send_mail('arch: Package [%s] added to Todolist' % todo.pkg.pkgname,
            t.render(c),
            'Arch Website Notification <nobody@archlinux.org>',
            [m.email for m in maints],
            fail_silently=True)

def public_list(request):
    todo_lists = Todolist.objects.incomplete()
    return direct_to_template(request, "todolists/public_list.html",
            {"todo_lists": todo_lists})


# vim: set ts=4 sw=4 et:
