from django import forms
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.simple import direct_to_template

from main.utils import make_choice
from .models import Mirror, MirrorUrl, MirrorProtocol

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
def generate_mirrorlist(request):
    if request.REQUEST.get('country', ''):
        form = MirrorlistForm(data=request.REQUEST)
        if form.is_valid():
            countries = form.cleaned_data['country']
            protocols = form.cleaned_data['protocol']
            return find_mirrors(request, countries, protocols)
    else:
        form = MirrorlistForm()

    return direct_to_template(request, 'mirrors/index.html', {'mirrorlist_form': form})

def find_mirrors(request, countries=None, protocols=None):
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
    return direct_to_template(request, 'mirrors/mirrorlist.txt', {
                'mirror_urls': qset,
            },
            mimetype='text/plain')

# vim: set ts=4 sw=4 et:
