from django import forms
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from main.models import Mirror, MirrorUrl
from main.utils import make_choice

class MirrorlistForm(forms.Form):
    country = forms.MultipleChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(MirrorlistForm, self).__init__(*args, **kwargs)
        mirrors = Mirror.objects.filter(active=True).values_list(
                'country', flat=True).distinct().order_by('country')
        self.fields['country'].choices = make_choice(
                        [mirror for mirror in mirrors])

@csrf_exempt
def generate(request):
    if request.REQUEST.get('country', ''):
        form = MirrorlistForm(data=request.REQUEST)
        if form.is_valid():
            countries = form.cleaned_data['country']
            return find_mirrors(request, countries)
    else:
        form = MirrorlistForm()

    return render_to_response('mirrors/index.html', {'mirrorlist_form': form},
                              context_instance=RequestContext(request))

def find_mirrors(request, countries=None):
    qset = MirrorUrl.objects.select_related().filter(
            Q(protocol__protocol__iexact='HTTP') |
            Q(protocol__protocol__iexact='FTP'),
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
