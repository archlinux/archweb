from main.models import Arch, Donor, MirrorUrl, News
from main.models import Package, Repo, ExternalProject
from . import utils

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import list_detail


def index(request):
    pkgs = utils.get_recent_updates()
    context = {
        'news_updates': News.objects.order_by('-postdate', '-id')[:10],
        'pkg_updates': pkgs,
    }
    return render_to_response('public/index.html', context,
                              context_instance=RequestContext(request))

def projects(request):
    return list_detail.object_list(request, 
            ExternalProject.objects.all(),
            template_name="public/projects.html",
            template_object_name="project")

def userlist(request, type='Developers'):
    users = User.objects.order_by('username')
    if type == 'Developers':
        users = users.filter(is_active=True).exclude(userprofile_user__roles="Trusted User")
        msg = "This is a list of the current Arch Linux Developers. They maintain the [core] and [extra] package repositories in addition to doing any other developer duties."
    elif type == 'Trusted Users':
        users = users.filter(is_active=True, userprofile_user__roles="Trusted User")
        msg = "Here are all your friendly Arch Linux Trusted Users who are in charge of the [community] repository."
    elif type == 'Fellows':
        users = users.filter(is_active=False)
        msg = "Below you can find a list of ex-developers (aka project fellows). These folks helped make Arch what it is today. Thanks!"

    context = {
        'user_type': type,
        'description': msg,
        'users': users,
    }
    return render_to_response('public/userlist.html', context,
                              context_instance=RequestContext(request))

def donate(request):
    donor_count = Donor.objects.count()
    donors = Donor.objects.order_by('name')
    splitval = donor_count / 4
    context = {
        'slice1': donors[:splitval],
        'slice2': donors[(splitval):(splitval*2)],
        'slice3': donors[(splitval*2):(donor_count-splitval)],
        'slice4': donors[(donor_count-splitval):donor_count],
    }
    return render_to_response('public/donate.html', context,
                              context_instance=RequestContext(request))

def download(request):
    qset = MirrorUrl.objects.filter(
            Q(protocol__protocol__iexact='HTTP') | Q(protocol__protocol__iexact='FTP'),
            mirror__public=True, mirror__active=True, mirror__isos=True
    )
    return list_detail.object_list(request, 
            qset.order_by('mirror__country', 'mirror__name'),
            template_name="public/download.html",
            template_object_name="mirror_url",
            extra_context={"path": request.path})

def feeds(request):
    context = {
        'arches': Arch.objects.all(),
        'repos': Repo.objects.all(),
    }
    return render_to_response('public/feeds.html', context)

# vim: set ts=4 sw=4 et:

