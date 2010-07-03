from django import forms
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from main.models import Mirror, MirrorUrl, MirrorProtocol
from main.utils import make_choice

class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False)
    protocol = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        mirrors = Mirror.objects.filter(active=True).values_list(
                'country', flat=True).distinct().order_by('country')
        self.fields['country'].choices = make_choice(mirrors)
        self.fields['country'].initial = ['Any']
        protos = make_choice(
                MirrorProtocol.objects.exclude(protocol__iexact='rsync'))
        self.fields['protocol'].choices = protos
        self.fields['protocol'].initial = [t[0] for t in protos]

@csrf_exempt
def generate(request):
    if request.REQUEST.get('country', ''):
        form = MirrorlistForm(data=request.REQUEST)
        if form.is_valid():
            countries = form.cleaned_data['country']
            protocols = form.cleaned_data['protocol']
            return find_mirrors(request, countries, protocols)
    else:
        form = MirrorlistForm()

    return render_to_response('mirrors/index.html', {'mirrorlist_form': form},
                              context_instance=RequestContext(request))

def find_mirrors(request, countries=None, protocols=None):
    print 'protocols', protocols
    if not protocols:
        protocols = MirrorProtocol.objects.exclude(
                protocol__iexact='rsync').values_list('protocol', flat=True)
    qset = MirrorUrl.objects.select_related().filter(
            protocol__protocol__in=protocols,
            mirror__public=True, mirror__active=True, mirror__isos=True
    )
    if countries and 'all' not in countries:
        qset = qset.filter(mirror__country__in=countries)
    qset = qset.order_by('mirror__country', 'mirror__name', 'url')
    res = render_to_response('mirrors/mirrorlist.txt', {
                'mirror_urls': qset,
            },
            mimetype='text/plain',
            context_instance=RequestContext(request))
    return res

# vim: set ts=4 sw=4 et:
