from django.http import HttpResponse, HttpResponseRedirect
from django.forms import ModelForm, RadioSelect, CheckboxSelectMultiple
from django.forms import ModelChoiceField
from isotests.models import Iso, Architecture, IsoType, BootType
from isotests.models import HardwareType, InstallType, Source, Test
from isotests.models import ClockChoice, Filesystem, Module, Bootloader
from django.template import Context, loader
from django.views.generic.simple import direct_to_template

class TestForm(ModelForm):
    class Meta:
        model = Test
        widgets = {
            "architecture": RadioSelect(),
            "iso_type": RadioSelect(),
            "boot_type": RadioSelect(),
            "hardware_type": RadioSelect(),
            "install_type": RadioSelect(),
            "source": RadioSelect(),
            "clock_choice": RadioSelect(),
            "filesystem": RadioSelect(),
            "rollback_filesystem": RadioSelect(),
            "bootloader": RadioSelect(),
            "modules": CheckboxSelectMultiple(),
            "rollback_modules": CheckboxSelectMultiple(),
        }
    iso = ModelChoiceField(queryset=Iso.objects.filter(active=True))

def add_result(request):
    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/isotests')
    else:
        form = TestForm()

    context = {'form': form}
    return direct_to_template(request, 'isotests/add.html', context)

def view_results(request):
    architecture_list = Architecture.objects.all()
    iso_type_list = IsoType.objects.all()
    boot_type_list = BootType.objects.all()
    hardware_type_list = HardwareType.objects.all()
    install_type_list = InstallType.objects.all()
    source_list = Source.objects.all()
    clock_choice_list = ClockChoice.objects.all()
    module_list = Module.objects.all()
    filesystem_list = Filesystem.objects.all()
    bootloader_list = Bootloader.objects.all()

    t = loader.get_template("isotests/results.html")
    c = Context({
            'architecture_list': architecture_list,
            'iso_type_list': iso_type_list,
            'boot_type_list': boot_type_list,
            'hardware_type_list': hardware_type_list,
            'install_type_list': install_type_list,
            'source_list': source_list,
            'clock_choices_list': clock_choice_list,
            'filesystem_list': filesystem_list,
            'module_list': module_list,
            'bootloader_list': bootloader_list,
    })
    return HttpResponse(t.render(c))
