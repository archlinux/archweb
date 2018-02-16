import operator
import time
from datetime import timedelta

from django.contrib import admin
from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Count, Max
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_text
from django.utils.http import http_date
from django.utils.timezone import now
from django.views.decorators.cache import never_cache
from main.models import Arch, Package, Repo
from news.models import News
from packages.models import FlagRequest, PackageRelation, Signoff
from packages.utils import get_signoff_groups
from todolists.models import TodolistPackage
from todolists.utils import get_annotated_todolists

from .forms import NewUserForm, ProfileForm, UserProfileForm
from .models import UserProfile
from .reports import available_reports
from .utils import get_annotated_maintainers


@login_required
def index(request):
    """The developer dashboard."""
    if request.user.is_authenticated():
        inner_q = PackageRelation.objects.filter(user=request.user)
    else:
        inner_q = PackageRelation.objects.none()
    inner_q = inner_q.values('pkgbase')

    flagged = Package.objects.normal().filter(
        flag_date__isnull=False, pkgbase__in=inner_q).order_by('pkgname')

    todopkgs = TodolistPackage.objects.select_related(
        'todolist', 'pkg', 'arch', 'repo').exclude(
            status=TodolistPackage.COMPLETE).filter(removed__isnull=True)
    todopkgs = todopkgs.filter(pkgbase__in=inner_q).order_by('todolist__name',
                                                             'pkgname')

    todolists = get_annotated_todolists(incomplete_only=True)

    signoffs = sorted(
        get_signoff_groups(user=request.user),
        key=operator.attrgetter('pkgbase'))

    page_dict = {
        'todos': todolists,
        'flagged': flagged,
        'todopkgs': todopkgs,
        'signoffs': signoffs,
        'reports': available_reports(),
    }

    return render(request, 'devel/index.html', page_dict)


@login_required
def stats(request):
    """The second half of the dev dashboard."""
    arches = Arch.objects.all().annotate(
        total_ct=Count('packages'),
        flagged_ct=Count('packages__flag_date'))
    repos = Repo.objects.all().annotate(
        total_ct=Count('packages'),
        flagged_ct=Count('packages__flag_date'))
    # the join is huge unless we do this separately, so merge the result here
    repo_maintainers = dict(Repo.objects.order_by().filter(
        userprofile__user__is_active=True).values_list('id').annotate(Count(
            'userprofile')))
    for repo in repos:
        repo.maintainer_ct = repo_maintainers.get(repo.id, 0)

    maintainers = get_annotated_maintainers()

    maintained = PackageRelation.objects.filter(
        type=PackageRelation.MAINTAINER).values('pkgbase')
    total_orphans = Package.objects.exclude(pkgbase__in=maintained).count()
    total_flagged_orphans = Package.objects.filter(
        flag_date__isnull=False).exclude(pkgbase__in=maintained).count()
    total_updated = Package.objects.filter(packager__isnull=True).count()
    orphan = {
        'package_count': total_orphans,
        'flagged_count': total_flagged_orphans,
        'updated_count': total_updated,
    }

    page_dict = {
        'arches': arches,
        'repos': repos,
        'maintainers': maintainers,
        'orphan': orphan,
    }

    return render(request, 'devel/stats.html', page_dict)

SELECTED_GROUPS = ['Developers', 'Trusted Users', 'Support Staff']

@login_required
def clock(request):
    groups = Group.objects.filter(name__in=SELECTED_GROUPS)
    devs = User.objects.filter(is_active=True).filter(groups__in=groups).order_by(
        'first_name', 'last_name').select_related('userprofile').distinct()

    latest_news = dict(News.objects.filter(author__is_active=True).values_list(
        'author').order_by().annotate(last_post=Max('postdate')))
    latest_package = dict(Package.objects.filter(
        packager__is_active=True).values_list('packager').order_by().annotate(
            last_build=Max('build_date')))
    latest_signoff = dict(Signoff.objects.filter(
        user__is_active=True).values_list('user').order_by().annotate(
            last_signoff=Max('created')))
    # The extra() bit ensures we can use our 'user_id IS NOT NULL' index
    latest_flagreq = dict(FlagRequest.objects.filter(
        user__is_active=True).extra(where=['user_id IS NOT NULL']).values_list(
            'user_id').order_by().annotate(last_flagrequest=Max('created')))
    latest_log = dict(LogEntry.objects.filter(
        user__is_active=True).values_list('user').order_by().annotate(
            last_log=Max('action_time')))

    for dev in devs:
        dates = [
            latest_news.get(dev.id, None),
            latest_package.get(dev.id, None),
            latest_signoff.get(dev.id, None),
            latest_flagreq.get(dev.id, None),
            latest_log.get(dev.id, None),
            dev.last_login,
        ]
        dates = [d for d in dates if d is not None]
        if dates:
            dev.last_action = max(dates)
        else:
            dev.last_action = None

    current_time = now()
    page_dict = {'developers': devs, 'utc_now': current_time, }

    response = render(request, 'devel/clock.html', page_dict)
    if not response.has_header('Expires'):
        expire_time = current_time.replace(second=0, microsecond=0)
        expire_time += timedelta(minutes=1)
        expire_time = time.mktime(expire_time.timetuple())
        response['Expires'] = http_date(expire_time)
    return response


@login_required
@never_cache
def change_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.POST:
        form = ProfileForm(request.POST)
        profile_form = UserProfileForm(request.POST,
                                       request.FILES,
                                       instance=profile)
        if form.is_valid() and profile_form.is_valid():
            request.user.email = form.cleaned_data['email']
            if form.cleaned_data['passwd1']:
                request.user.set_password(form.cleaned_data['passwd1'])
            with transaction.atomic():
                request.user.save()
                profile_form.save()
            return HttpResponseRedirect('/devel/')
    else:
        form = ProfileForm(initial={'email': request.user.email})
        profile_form = UserProfileForm(instance=profile)
    return render(request, 'devel/profile.html',
                  {'form': form,
                   'profile_form': profile_form})


@login_required
def report(request, report_name, username=None):
    available = {report.slug: report for report in available_reports()}
    report = available.get(report_name, None)
    if report is None:
        raise Http404

    packages = Package.objects.normal()
    user = None
    if username:
        user = get_object_or_404(User, username=username, is_active=True)
        maintained = PackageRelation.objects.filter(
            user=user, type=PackageRelation.MAINTAINER).values('pkgbase')
        packages = packages.filter(pkgbase__in=maintained)

    maints = User.objects.filter(id__in=PackageRelation.objects.filter(
        type=PackageRelation.MAINTAINER).values('user'))

    if report.slug == 'uncompressed-man' or report.slug == 'uncompressed-info':
        packages = report.packages(packages, username)
    else:
        packages = report.packages(packages)

    arches = {pkg.arch for pkg in packages}
    repos = {pkg.repo for pkg in packages}
    context = {
        'all_maintainers': maints,
        'title': report.description,
        'report': report,
        'maintainer': user,
        'packages': packages,
        'arches': sorted(arches),
        'repos': sorted(repos),
        'column_names': report.names,
        'column_attrs': report.attrs,
    }
    return render(request, 'devel/packages.html', context)


def log_addition(request, obj):
    """Cribbed from ModelAdmin.log_addition."""
    LogEntry.objects.log_action(
        user_id=request.user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=force_text(obj),
        action_flag=ADDITION,
        change_message="Added via Create New User form.")


@permission_required('auth.add_user')
@never_cache
def new_user_form(request):
    if request.POST:
        form = NewUserForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                log_addition(request, form.instance.user)
            return HttpResponseRedirect('/admin/auth/user/%d/' % \
                    form.instance.user.id)
    else:
        form = NewUserForm()

    context = {
        'description': '''A new user will be created with the
            following properties in their profile. A random password will be
            generated and the user will be e-mailed with their account details
            n plaintext.''',
        'form': form,
        'title': 'Create User',
        'submit_text': 'Create User'
    }
    return render(request, 'general_form.html', context)


@user_passes_test(lambda u: u.is_superuser)
def admin_log(request, username=None):
    user = None
    if username:
        user = get_object_or_404(User, username=username)
    context = {'title': "Admin Action Log", 'log_user': user, }
    context.update(admin.site.each_context(request))
    return render(request, 'devel/admin_log.html', context)

# vim: set ts=4 sw=4 et:
