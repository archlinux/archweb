import json
from operator import attrgetter

from django import forms
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.utils.timezone import now
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, ListView

from api.deprecation import deprecated_json_endpoint
from main.models import Package
from main.utils import find_unique_slug
from packages.utils import PackageJSONEncoder, attach_maintainers

from .models import Todolist, TodolistPackage
from .stages import STAGES
from .utils import attach_staging, get_annotated_todolists


class TodoListForm(forms.ModelForm):
    raw = forms.CharField(label='Packages', required=False,
                          help_text='(one per line)',
                          widget=forms.Textarea(attrs={'rows': '20', 'cols': '60'}))
    stages = forms.MultipleChoiceField(
        choices=[(stage.key, stage.name) for stage in STAGES.values()],
        initial=Todolist.DEFAULT_STAGES[Todolist.REBUILD],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-list'}),
        help_text='(cannot be changed later)')

    field_order = ('name', 'kind', 'stages', 'description', 'raw')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # stages are immutable once a todo list has been created
        if self.instance.pk:
            del self.fields['stages']

    def selected_stages(self):
        return [key for key in STAGES if key in self.cleaned_data['stages']]

    def package_names(self):
        return {s.strip() for s in self.cleaned_data['raw'].split("\n")}

    def packages(self):
        return Package.objects.normal().filter(
            pkgname__in=self.package_names(),
            repo__testing=False, repo__staging=False).order_by('arch')

    class Meta:
        model = Todolist
        fields = ('name', 'kind', 'description', 'raw')


@never_cache
def flag(request, slug, pkg_id):
    todolist = get_object_or_404(Todolist, slug=slug)
    tlpkg = get_object_or_404(TodolistPackage, id=pkg_id, todolist=todolist,
                              removed__isnull=True)
    stage = todolist.current_stage
    if stage is None or not stage.per_package:
        return HttpResponseBadRequest('The current stage does not track package completion')
    # TODO: none of this; require absolute value on submit
    if tlpkg.is_complete:
        tlpkg.progress = todolist.progress
    else:
        tlpkg.progress = todolist.progress + 1
    tlpkg.user = request.user
    tlpkg.save(update_fields=('progress', 'user', 'last_modified'))
    if tlpkg.is_complete and todolist.can_advance():
        send_stage_complete_email(todolist, stage)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'status': tlpkg.status_str,
            'css_class': tlpkg.status_css_class(),
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    return redirect(todolist)


@never_cache
@require_POST
@transaction.atomic
def advance(request, slug):
    todolist = get_object_or_404(Todolist.objects.select_for_update(), slug=slug)
    if not todolist.can_advance():
        return HttpResponseBadRequest('The todo list cannot proceed to the next stage')
    todolist.progress += 1
    todolist.save(update_fields=('progress', 'last_modified'))
    todolist.todolistpackage_set.filter(
        removed__isnull=True, progress__lt=todolist.progress).update(
        progress=todolist.progress)
    stage = todolist.current_stage
    if stage and stage.per_package:
        send_todolist_emails(todolist, todolist.incomplete_packages(), stage)
    return redirect(todolist)


@never_cache
@require_POST
@transaction.atomic
def back(request, slug):
    todolist = get_object_or_404(Todolist.objects.select_for_update(), slug=slug)
    if todolist.progress == 0:
        return HttpResponseBadRequest('The todo list is in its first stage')
    # packages keep their progress, going back does not invalidate it
    todolist.progress -= 1
    todolist.save(update_fields=('progress', 'last_modified'))
    return redirect(todolist)


def view(request, slug):
    todolist = get_object_or_404(Todolist, slug=slug)
    # we don't hold onto the result, but the objects are the same here,
    # so accessing maintainers in the template is now cheap
    attach_maintainers(todolist.packages())
    attach_staging(todolist.packages(), todolist.pk)
    arches = {tp.arch for tp in todolist.packages()}
    repos = {tp.repo for tp in todolist.packages()}
    stage = todolist.current_stage
    context = {
        'list': todolist,
        'arches': sorted(arches),
        'repos': sorted(repos),
        # package status is only meaningful in stages with per-package completion
        'per_package': stage is not None and stage.per_package,
    }
    return render(request, 'todolists/view.html', context)


def list_pkgbases(request, slug):
    '''Used to make bulk moves of packages a lot easier.'''
    todolist = get_object_or_404(Todolist, slug=slug)
    pkgbases = TodolistPackage.objects.values_list(
        'pkgbase', flat=True).filter(
        todolist=todolist, removed__isnull=True).order_by(
        'pkgbase').distinct()
    return HttpResponse('\n'.join(pkgbases), content_type='text/plain')


class TodolistListView(ListView):
    context_object_name = "lists"
    template_name = "todolists/list.html"
    paginate_by = 50

    def get_queryset(self):
        return get_annotated_todolists()


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
        'default_stages': Todolist.DEFAULT_STAGES,
        'submit_text': 'Create List'
    }
    return render(request, 'todolists/form.html', page_dict)


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
        'title': f'Edit Todo List: {todo_list.name}',
        'description': '',
        'form': form,
        'submit_text': 'Save List'
    }
    return render(request, 'todolists/form.html', page_dict)


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
        todolist.stages = form.selected_stages()
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
            'progress': todolist.progress,
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
                todo_pkg.progress = todolist.progress
                save = True
            if todo_pkg.pkg != package:
                todo_pkg.pkg = package
                save = True
            if save:
                todo_pkg.save()

    return todo_pkgs


def send_todolist_emails(todo_list, todo_packages, stage=None):
    '''Sends emails to package maintainers notifying them that packages have
    been added to a todo list, or that the todo list reached a stage which
    asks for per-package completion. Nothing is sent before the first such
    stage has been reached.'''
    if not todo_list.per_package_reached():
        return
    # start by flipping the incoming list on its head: we want a list of
    # involved maintainers and the packages they need to be notified about.
    orphan_packages = []
    maint_packages = {}
    for todo_package in todo_packages:
        if todo_package.pkg is None:
            continue
        maints = todo_package.pkg.maintainers.values_list('email', flat=True)
        if not maints:
            orphan_packages.append(todo_package)
        else:
            for maint in maints:
                maint_packages.setdefault(maint, []).append(todo_package)

    for maint, packages in maint_packages.items():
        packages = sorted(packages, key=attrgetter('pkgname', 'arch'))
        ctx = {
            'todo_packages': packages,
            'todolist': todo_list,
            'stage': stage,
        }
        if stage:
            subject = f'Todo list \'{todo_list.name}\' reached stage \'{stage.name}\''
        else:
            subject = f'Packages added to todo list \'{todo_list.name}\''
        template = loader.get_template('todolists/email_notification.txt')
        send_mail(subject,
                  template.render(ctx),
                  'Arch Website Notification <nobody@archlinux.org>',
                  [maint],
                  fail_silently=True)


def send_stage_complete_email(todo_list, stage):
    '''Notifies the todo list creator that all packages completed a stage.'''
    ctx = {
        'todolist': todo_list,
        'stage': stage,
    }
    template = loader.get_template('todolists/complete_email_notification.txt')
    send_mail(f'All packages on the todo list \'{todo_list.name}\' completed stage \'{stage.name}\'',
              template.render(ctx),
              'Arch Website Notification <nobody@archlinux.org>',
              [todo_list.creator.email],
              fail_silently=True)


class TodoListJSONEncoder(PackageJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Todolist):
            return {
                'id': obj.pk,
                'name': obj.name,
                'description': obj.description,
                'created': obj.created,
                'last_modified': obj.last_modified,
                'packages': [tpkg for tpkg in obj.packages() if tpkg.pkg],
                'kind': obj.kind_str
            }

        return super().default(obj)


@deprecated_json_endpoint('/api/v1/todo/{slug}/')
def view_json(request, slug):
    todolist = get_object_or_404(Todolist, slug=slug)
    to_json = json.dumps(todolist, ensure_ascii=False, cls=TodoListJSONEncoder)
    return HttpResponse(to_json, content_type='application/json')

# vim: set ts=4 sw=4 et:
