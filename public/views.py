from main.models import Arch, Repo, Donor, News
from mirrors.models import MirrorUrl
from . import utils

from django.contrib.auth.models import User
from django.db.models import Q
from django.views.generic import list_detail
from django.views.generic.simple import direct_to_template


def index(request):
    pkgs = utils.get_recent_updates()
    context = {
        'news_updates': News.objects.order_by('-postdate', '-id')[:10],
        'pkg_updates': pkgs,
    }
    return direct_to_template(request, 'public/index.html', context)

def userlist(request, type='Developers'):
    users = User.objects.order_by('username')
    if type == 'Developers':
        users = users.filter(is_active=True, groups__name="Developers")
        msg = "This is a list of the current Arch Linux Developers. They maintain the [core] and [extra] package repositories in addition to doing any other developer duties."
    elif type == 'Trusted Users':
        users = users.filter(is_active=True, groups__name="Trusted Users")
        msg = "Here are all your friendly Arch Linux Trusted Users who are in charge of the [community] repository."
    elif type == 'Fellows':
        users = users.filter(is_active=False)
        msg = "Below you can find a list of ex-developers (aka project fellows). These folks helped make Arch what it is today. Thanks!"

    context = {
        'user_type': type,
        'description': msg,
        'users': users,
    }
    return direct_to_template(request, 'public/userlist.html', context)

def donate(request):
    context = {
        'donors': Donor.objects.order_by('name'),
    }
    return direct_to_template(request, 'public/donate.html', context)

def download(request):
    qset = MirrorUrl.objects.filter(
            Q(protocol__protocol__iexact='HTTP') | Q(protocol__protocol__iexact='FTP'),
            mirror__public=True, mirror__active=True, mirror__isos=True
    )
    return list_detail.object_list(request, 
            qset.order_by('mirror__country', 'mirror__name', 'protocol'),
            template_name="public/download.html",
            template_object_name="mirror_url")

def feeds(request):
    context = {
        'arches': Arch.objects.all(),
        'repos': Repo.objects.all(),
    }
    return direct_to_template(request, 'public/feeds.html', context)

# vim: set ts=4 sw=4 et:
