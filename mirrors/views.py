from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from main.models import Mirror, MirrorUrl
from main.utils import make_choice

class MirrorlistForm(forms.Form):
    country = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        mirrors = Mirror.objects.values_list(
                'country', flat=True).distinct().order_by('country')
        self.fields['country'].choices = [('all', 'All')] + make_choice(
                        [mirror for mirror in mirrors])


def choose(request):
    if request.POST:
        form = MirrorlistForm(data=request.POST)
        if form.is_valid():
            country = form.cleaned_data['country']
            return HttpResponseRedirect(reverse(generate,
                kwargs = { 'country' : country }))
    else:
        form = MirrorlistForm()

    return render_to_response('mirrors/index.html', {'mirrorlist_form': form},
                              context_instance=RequestContext(request))

def generate(request, country=None):
    qset = MirrorUrl.objects.select_related().filter(
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
            },
            mimetype='text/plain')
    return res

# vim: set ts=4 sw=4 et:
