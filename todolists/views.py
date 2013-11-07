import json

from django import forms
from django.http import HttpResponse
from django.core.mail import send_mail
from django.shortcuts import (get_list_or_404, get_object_or_404,
        redirect, render)
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.views.generic import DeleteView
from django.template import Context, loader
from django.utils.timezone import now

from main.models import Package, Repo
from main.utils import find_unique_slug
from packages.utils import attach_maintainers
from .models import Todolist, TodolistPackage
from .utils import get_annotated_todolists, attach_staging


class TodoListForm(forms.ModelForm):
    raw = forms.CharField(label='Packages', required=False,
            help_text='(one per line)',
            widget=forms.Textarea(attrs={'rows': '20', 'cols': '60'}))

    def package_names(self):
        return {s.strip() for s in self.cleaned_data['raw'].split("\n")}

    def packages(self):
        return Package.objects.normal().filter(
                pkgname__in=self.package_names(),
                repo__testing=False, repo__staging=False).order_by('arch')

    class Meta:
        model = Todolist
        fields = ('name', 'description', 'raw')


@never_cache
def flag(request, slug, pkg_id):
    todolist = get_object_or_404(Todolist, slug=slug)
    tlpkg = get_object_or_404(TodolistPackage, id=pkg_id, removed__isnull=True)
    # TODO: none of this; require absolute value on submit
    if tlpkg.status == TodolistPackage.INCOMPLETE:
        tlpkg.status = TodolistPackage.COMPLETE
    else:
        tlpkg.status = TodolistPackage.INCOMPLETE
    tlpkg.user = request.user
    tlpkg.save(update_fields=('status', 'user', 'last_modified'))
    if request.is_ajax():
        data = {
            'status': tlpkg.get_status_display(),
            'css_class': tlpkg.status_css_class(),
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    return redirect(todolist)


def view_redirect(request, old_id):
    todolist = get_object_or_404(Todolist, old_id=old_id)
    return redirect(todolist, permanent=True)


def view(request, slug):
    todolist = get_object_or_404(Todolist, slug=slug)
    svn_roots = Repo.objects.values_list(
            'svn_root', flat=True).order_by().distinct()
    # we don't hold onto the result, but the objects are the same here,
    # so accessing maintainers in the template is now cheap
    attach_maintainers(todolist.packages())
    attach_staging(todolist.packages(), todolist.pk)
    arches = {tp.arch for tp in todolist.packages()}
    repos = {tp.repo for tp in todolist.packages()}
    context = {
        'list': todolist,
        'svn_roots': svn_roots,
        'arches': sorted(arches),
        'repos': sorted(repos),
    }
    return render(request, 'todolists/view.html', context)


def list_pkgbases(request, slug, svn_root):
    '''Used to make bulk moves of packages a lot easier.'''
    todolist = get_object_or_404(Todolist, slug=slug)
    repos = get_list_or_404(Repo, svn_root=svn_root)
    pkgbases = TodolistPackage.objects.values_list(
            'pkgbase', flat=True).filter(
            todolist=todolist, repo__in=repos, removed__isnull=True).order_by(
            'pkgbase').distinct()
    return HttpResponse('\n'.join(pkgbases), content_type='text/plain')


def todolist_list(request):
    incomplete_only = request.user.is_anonymous()
    lists = get_annotated_todolists(incomplete_only)
    return render(request, 'todolists/list.html', {'lists': lists})


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
            'description': '',
            'form': form,
            'submit_text': 'Create List'
    }
    return render(request, 'general_form.html', page_dict)


# TODO: this calls for transaction management and async emailing
@never_cache
def edit(request, slug):
    todo_list = get_object_or_404(Todolist, slug=slug)
    if request.POST:
        form = TodoListForm(request.POST, instance=todo_list)
        if form.is_valid():
            new_packages = create_todolist_packages(form)
            send_todolist_emails(todo_list, new_packages)
            return redirect(todo_list)
    else:
        form = TodoListForm(instance=todo_list,
                initial={'packages': todo_list.raw})

    page_dict = {
            'title': 'Edit Todo List: %s' % todo_list.name,
            'description': '',
            'form': form,
            'submit_text': 'Save List'
    }
    return render(request, 'general_form.html', page_dict)


class DeleteTodolist(DeleteView):
    model = Todolist
    # model in main == assumes name 'main/todolist_confirm_delete.html'
    template_name = 'todolists/todolist_confirm_delete.html'
    success_url = '/todo/'


@transaction.atomic
def create_todolist_packages(form, creator=None):
    package_names = form.package_names()
    packages = form.packages()
    timestamp = now()
    if creator:
        # todo list is new, populate creator and slug fields
        todolist = form.save(commit=False)
        todolist.creator = creator
        todolist.slug = find_unique_slug(Todolist, todolist.name)
        todolist.save()
    else:
        # todo list already existed
        form.save()
        todolist = form.instance

        # first mark removed any packages not in the new list
        to_remove = set()
        for todo_pkg in todolist.packages():
            if todo_pkg.pkg and todo_pkg.pkg not in packages:
                to_remove.add(todo_pkg.pk)
            elif todo_pkg.pkgname not in package_names:
                to_remove.add(todo_pkg.pk)

        TodolistPackage.objects.filter(
                pk__in=to_remove).update(removed=timestamp)

    # Add (or mark unremoved) any packages in the new packages list
    todo_pkgs = []
    for package in packages:
        # ensure get_or_create uses the fields in our unique constraint
        defaults = {
            'pkg': package,
            'pkgbase': package.pkgbase,
            'repo':  package.repo,
        }
        todo_pkg, created = TodolistPackage.objects.get_or_create(
                todolist=todolist,
                pkgname=package.pkgname,
                arch=package.arch,
                defaults=defaults)
        if created:
            todo_pkgs.append(todo_pkg)
        else:
            save = False
            if todo_pkg.removed is not None:
                todo_pkg.removed = None
                save = True
            if todo_pkg.pkg != package:
                todo_pkg.pkg = package
                save = True
            if save:
                todo_pkg.save()

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

# vim: set ts=4 sw=4 et:
