# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.forms import ModelForm
from isotests.models import Test
from django.shortcuts import render_to_response
from django.template import RequestContext

class TestForm(ModelForm):
    class Meta:
        model = Test

def add_result(request):
    if request.method == 'POST': # If the form has been submitted...
        form = TestForm(request.POST) # A form bound to the post data
        if form.is_valid(): # All validation rules pass
            form.save()
            return HttpResponseRedirect('/isotests') # Redirect after POST
    else:
        form = TestForm() # An unbound form

    return render_to_response('isotests/add.html', {
            'form': form,
            },
                              context_instance=RequestContext(request))
