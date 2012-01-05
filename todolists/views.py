from django import forms

from django.http import HttpResponse
from django.core.mail import send_mail
from django.shortcuts import get_list_or_404, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.views.generic import DeleteView
from django.views.generic.simple import direct_to_template
from django.template import Context, loader
from django.utils import simplejson

from main.models import Todolist, TodolistPkg, Package, Repo
from packages.utils import attach_maintainers
from .utils import get_annotated_todolists

class TodoListForm(forms.ModelForm):
    packages = forms.CharField(required=False,
            help_text='(one per line)',
            widget=forms.Textarea(attrs={'rows': '20', 'cols': '60'}))

    def clean_packages(self):
        package_names = [s.strip() for s in
                self.cleaned_data['packages'].split("\n")]
        package_names = set(package_names)
        packages = Package.objects.filter(pkgname__in=package_names).filter(
                repo__testing=False, repo__staging=False).select_related(
                        'arch', 'repo').order_by('arch')
        return packages

    class Meta:
        model = Todolist
        fields = ('name', 'description')

@permission_required('main.change_todolistpkg')
@never_cache
def flag(request, list_id, pkg_id):
    todolist = get_object_or_404(Todolist, id=list_id)
    pkg = get_object_or_404(TodolistPkg, id=pkg_id)
    pkg.complete = not pkg.complete
    pkg.save()
    if request.is_ajax():
        return HttpResponse(
            simplejson.dumps({'complete': pkg.complete}),
            mimetype='application/json')
    return redirect(todolist)

@login_required
def view(request, list_id):
    todolist = get_object_or_404(Todolist, id=list_id)
    svn_roots = Repo.objects.order_by().values_list(
            'svn_root', flat=True).distinct()
    # we don't hold onto the result, but the objects are the same here,
    # so accessing maintainers in the template is now cheap
    attach_maintainers(tp.pkg for tp in todolist.packages)
    return direct_to_template(request, 'todolists/view.html', {
        'list': todolist,
        'svn_roots': svn_roots,
    })

# really no need for login_required on this one...
def list_pkgbases(request, list_id, svn_root):
    '''Used to make bulk moves of packages a lot easier.'''
    todolist = get_object_or_404(Todolist, id=list_id)
    repos = get_list_or_404(Repo, svn_root=svn_root)
    pkgbases = set(tp.pkg.pkgbase for tp in todolist.packages
            if tp.pkg.repo in repos)
    return HttpResponse('\n'.join(sorted(pkgbases)),
        mimetype='text/plain')

@login_required
def todolist_list(request):
    lists = get_annotated_todolists()
    return direct_to_template(request, 'todolists/list.html', {'lists': lists})

@permission_required('main.add_todolist')
@never_cache
def add(request):
    if request.POST:
        form = TodoListForm(request.POST)
        if form.is_valid():
            new_packages = create_todolist_packages(form, creator=request.user)
            send_todolist_emails(form.instance, new_packages)
            return redirect(form.instance)
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
        form = TodoListForm(request.POST, instance=todo_list)
        if form.is_valid():
            new_packages = create_todolist_packages(form)
            send_todolist_emails(todo_list, new_packages)
            return redirect(todo_list)
    else:
        form = TodoListForm(instance=todo_list,
                initial={ 'packages': '\n'.join(todo_list.package_names) })

    page_dict = {
            'title': 'Edit Todo List: %s' % todo_list.name,
            'form': form,
            'submit_text': 'Save List'
    }
    return direct_to_template(request, 'general_form.html', page_dict)

class DeleteTodolist(DeleteView):
    model = Todolist
    # model in main == assumes name 'main/todolist_confirm_delete.html'
    template_name = 'todolists/todolist_confirm_delete.html'
    success_url = '/todo/'

@transaction.commit_on_success
def create_todolist_packages(form, creator=None):
    packages = form.cleaned_data['packages']
    if creator:
        # todo list is new
        todolist = form.save(commit=False)
        todolist.creator = creator
        todolist.save()

        old_packages = []
    else:
        # todo list already existed
        form.save()
        todolist = form.instance
        # first delete any packages not in the new list
        for todo_pkg in todolist.packages:
            if todo_pkg.pkg not in packages:
                todo_pkg.delete()

        # save the old package list so we know what to add
        old_packages = [p.pkg for p in todolist.packages]

    todo_pkgs = []
    for package in packages:
        if package not in old_packages:
            todo_pkg = TodolistPkg.objects.create(list=todolist, pkg=package)
            todo_pkgs.append(todo_pkg)

    return todo_pkgs

def send_todolist_emails(todo_list, new_packages):
    '''Sends emails to package maintainers notifying them that packages have
    been added to a todo list.'''
    # start by flipping the incoming list on its head: we want a list of
    # involved maintainers and the packages they need to be notified about.
    orphan_packages = []
    maint_packages = {}
    for todo_package in new_packages:
        maints = todo_package.pkg.maintainers.values_list('email', flat=True)
        if not maints:
            orphan_packages.append(todo_package)
        else:
            for maint in maints:
                maint_packages.setdefault(maint, []).append(todo_package)

    for maint, packages in maint_packages.iteritems():
        ctx = Context({
            'todo_packages': sorted(packages),
            'todolist': todo_list,
        })
        template = loader.get_template('todolists/email_notification.txt')
        send_mail('Packages added to todo list \'%s\'' % todo_list.name,
                template.render(ctx),
                'Arch Website Notification <nobody@archlinux.org>',
                [maint],
                fail_silently=True)

def public_list(request):
    todo_lists = Todolist.objects.incomplete()
    # total hackjob, but it makes this a lot less query-intensive.
    all_pkgs = [tp for tl in todo_lists for tp in tl.packages]
    attach_maintainers([tp.pkg for tp in all_pkgs])
    return direct_to_template(request, "todolists/public_list.html",
            {"todo_lists": todo_lists})

# vim: set ts=4 sw=4 et:
