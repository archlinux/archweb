from django.contrib.auth.models import User
from archweb.main.models import AltForum, Arch, Donor, MirrorUrl, News
from archweb.main.models import Package, Repo, ExternalProject
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic import list_detail


def index(request):
    context = {
        'news': News.objects.order_by('-postdate', '-id')[:10],
        'pkgs': Package.objects.exclude(repo__name__iexact='testing').order_by(
                '-last_update')[:15],
        'repos': Repo.objects.all()
    }
    return render_to_response('public/index.html', RequestContext(request, 
                                                                  context))

def about(request):
    return render_to_response('public/about.html')

def art(request):
    return render_to_response('public/art.html')

def svn(request):
    return render_to_response('public/svn.html')

def projects(request):
    projects = ExternalProject.objects.all()
    return render_to_response('public/projects.html', {'projects': projects})

def developers(request):
    devs = User.objects.filter(is_active=True).exclude(userprofile_user__roles="Trusted User").order_by('username')
    tus = User.objects.filter(is_active=True, userprofile_user__roles="Trusted User").order_by('username')
    return render_to_response('public/developers.html',
            {'developers': devs, 'tus': tus})

def fellows(request):
    return list_detail.object_list(request, 
            User.objects.filter(is_active=False).order_by('username'),
            template_name="public/fellows.html",
            template_object_name="dev",
            extra_context={"dev_type": "Fellows",
                "description": "Below you can find a list of ex-developers"
                " (aka Project Fellows). These folks helped make Arch what"
                " it is today. Thanks!"})

def donate(request):
    donor_count = Donor.objects.count()
    donors = Donor.objects.order_by('name')
    splitval = donor_count / 4
    slice1 = donors[:splitval]
    slice2 = donors[(splitval):(splitval*2)]
    slice3 = donors[(splitval*2):(donor_count-splitval)]
    slice4 = donors[(donor_count-splitval):donor_count]
    return render_to_response('public/donate.html', 
        {'slice1':slice1,'slice2':slice2,'slice3':slice3,'slice4':slice4})

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

def irc(request):
    return render_to_response('public/irc.html')

def moreforums(request):
    return list_detail.object_list(request, 
            AltForum.objects.order_by('language', 'name'),
            template_name="public/moreforums.html",
            template_object_name="forum",
            extra_context={"path": request.path})

# vim: set ts=4 sw=4 et:

