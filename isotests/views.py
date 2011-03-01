# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.forms import ModelForm, DateField
from isotests.models import *
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader

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

    return render_to_response('isotests/add.html', { 'form': form, },
            context_instance=RequestContext(request))

def view_results(request):
    result_success_list = Test.objects.filter(success=True)
    result_failed_list = Test.objects.filter(success=False)

    architecture_list = Architecture.objects.all()
    isotype_list = Isotype.objects.all()
    boottype_list = Boottype.objects.all()
    hardware_list = Hardware.objects.all()
    installtype_list = InstallType.objects.all()
    source_list = Source.objects.all()
    clockchoice_list = Clockchoice.objects.all()
    module_list = Module.objects.all()
    filesystem_list = Filesystem.objects.all()
    bootloader_list = Bootloader.objects.all()

    t = loader.get_template("isotests/results.html")
    c = Context({
            'arch_choices': architecture_list,
            'isotype_choices': isotype_list,
            'boottype_choices': boottype_list,
            'hardware_list': hardware_list,
            'installtype_list': installtype_list,
            'source_list': source_list,
            'clock_choices': clockchoice_list,
            'filesystem_list': filesystem_list,
            'module_list': module_list,
            'bootloader_list': bootloader_list,
    })
    return HttpResponse(t.render(c))
