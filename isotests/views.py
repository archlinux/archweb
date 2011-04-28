from django.forms import ModelChoiceField, CharField, TextInput
from django.forms import ModelForm, RadioSelect, CheckboxSelectMultiple
from django.forms import ModelMultipleChoiceField, BooleanField
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Context, loader
from django.views.generic.simple import direct_to_template

from isotests.models import Iso, Architecture, IsoType, BootType
from isotests.models import HardwareType, InstallType, Source, Test
from isotests.models import ClockChoice, Filesystem, Module, Bootloader

class TestForm(ModelForm):
    class Meta:
        model = Test
        fields = ("user_name", "user_email", "iso", "architecture",
                  "iso_type", "boot_type", "hardware_type",
                  "install_type", "source", "clock_choice", "filesystem",
                  "modules", "rollback_filesystem", "rollback_modules",
                  "bootloader", "success", "comments")
        widgets = {
            "architecture": RadioSelect(),
            "iso_type": RadioSelect(),
            "boot_type": RadioSelect(),
            "hardware_type": RadioSelect(),
            "install_type": RadioSelect(),
            "source": RadioSelect(),
            "clock_choice": RadioSelect(),
            "bootloader": RadioSelect(),
            "modules": CheckboxSelectMultiple(),
        }
    success = BooleanField(help_text="Only check this if everything went fine. " \
            "If you you ran into any errors please specify them in the " \
            "comments.", required=False)
    iso = ModelChoiceField(queryset=Iso.objects.filter(active=True))
    filesystem = ModelChoiceField(queryset=Filesystem.objects.all(),
            help_text="Check the installed system, including fstab.",
            widget=RadioSelect())
    modules = ModelMultipleChoiceField(queryset=Module.objects.all(),
            help_text="", widget=CheckboxSelectMultiple(), required=False)
    rollback_filesystem = ModelChoiceField(queryset=Filesystem.objects.all(),
            help_text="If you did a rollback followed by a new attempt to setup " \
            "your lockdevices/filesystems, select which option you took here.",
            widget=RadioSelect(), required=False)
    rollback_modules = ModelMultipleChoiceField(queryset=Module.objects.all(),
            help_text="If you did a rollback followed b a new attempt to setup " \
            "your lockdevices/filesystems, select which option you took here.",
    widget=CheckboxSelectMultiple(), required=False)
    website = CharField(label='',
            widget=TextInput(attrs={'style': 'display:none;'}), required=False)

def add_result(request):
    if request.POST:
        form = TestForm(request.POST)
        if form.is_valid() and request.POST['website'] == '':
            form.save()
            return HttpResponseRedirect('/isotests/thanks/')
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

def view_results_iso(request, isoid):
    iso = Iso.objects.get(pk=isoid)
    test_list = Test.objects.filter(iso__pk=isoid)
    context = {
        'iso_name': iso.name,
        'test_list': test_list
    }
    return direct_to_template(request, 'isotests/result_list.html', context)

def view_results_for(request, option, value):
    kwargs = {option: value}
    test_list = Test.objects.filter(**kwargs).order_by("iso__name", "pk")
    context = {
        'option': option,
        'value': value,
        'test_list': test_list
    }
    return direct_to_template(request, 'isotests/result_list.html', context)

def thanks(request):
    return direct_to_template(request, "isotests/thanks.html", None)
