from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from archweb.main.models import Arch, Mirror, MirrorUrl
from archweb.main.utils import make_choice

class MirrorlistForm(forms.Form):
    arch = forms.ChoiceField(required=True)
    country = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        arches = Arch.objects.exclude(name__iexact='any').order_by('name')
        mirrors = Mirror.objects.values_list(
                'country', flat=True).distinct().order_by('country')
        self.fields['arch'].choices = make_choice(
                        [arch.name for arch in arches])
        self.fields['country'].choices = [('all', 'All')] + make_choice(
                        [mirror for mirror in mirrors])


def choose(request):
    if request.POST:
        form = MirrorlistForm(data=request.POST)
        if form.is_valid():
            arch = form.cleaned_data['arch']
            country = form.cleaned_data['country']
            return HttpResponseRedirect(reverse(generate,
                kwargs = {'arch' : arch, 'country' : country }))
    else:
        form = MirrorlistForm()

    return render_to_response('mirrors/index.html', {'mirrorlist_form': form})

def generate(request, arch='i686', country=None):
    # do a quick sanity check on the architecture
    archobj = get_object_or_404(Arch, name=arch)
    qset = MirrorUrl.objects.filter(
            Q(protocol__protocol__iexact='HTTP') |
            Q(protocol__protocol__iexact='FTP'),
            mirror__public=True, mirror__active=True, mirror__isos=True
    )
    if country and country != 'all':
        qset = qset.filter(mirror__country__iexact=country)
    qset = qset.order_by('mirror__country', 'mirror__name', 'url')
    res = render_to_response('mirrors/mirrorlist.txt',
            {
                'mirror_urls': qset,
                'arch': arch,
            },
            mimetype='text/plain')
    return res

# vim: set ts=4 sw=4 et:
