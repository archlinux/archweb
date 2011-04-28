from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic.simple import direct_to_template

from .models import (Architecture, BootType, Bootloader, ClockChoice,
        Filesystem, HardwareType, InstallType, Iso, IsoType, Module, Source,
        Test)

def standard_field(model, help_text=None):
    return forms.ModelChoiceField(queryset=model.objects.all(),
        widget=forms.RadioSelect(), empty_label=None, help_text=help_text)

class TestForm(forms.ModelForm):
    iso = forms.ModelChoiceField(queryset=Iso.objects.filter(active=True))
    architecture = standard_field(Architecture)
    iso_type = standard_field(IsoType)
    boot_type = standard_field(BootType)
    hardware_type = standard_field(HardwareType)
    install_type = standard_field(InstallType)
    source = standard_field(Source)
    clock_choice = standard_field(ClockChoice)
    bootloader = standard_field(Bootloader)
    filesystem = standard_field(Filesystem,
            help_text="Check the installed system, including fstab.")
    modules = forms.ModelMultipleChoiceField(queryset=Module.objects.all(),
            help_text="", widget=forms.CheckboxSelectMultiple(), required=False)
    rollback_filesystem = forms.ModelChoiceField(queryset=Filesystem.objects.all(),
            help_text="If you did a rollback followed by a new attempt to setup " \
            "your lockdevices/filesystems, select which option you took here.",
            widget=forms.RadioSelect(), required=False)
    rollback_modules = forms.ModelMultipleChoiceField(queryset=Module.objects.all(),
            help_text="If you did a rollback followed b a new attempt to setup " \
            "your lockdevices/filesystems, select which option you took here.",
            widget=forms.CheckboxSelectMultiple(), required=False)
    success = forms.BooleanField(help_text="Only check this if everything went fine. " \
            "If you you ran into any errors please specify them in the " \
            "comments.", required=False)
    website = forms.CharField(label='',
            widget=forms.TextInput(attrs={'style': 'display:none;'}), required=False)

    class Meta:
        model = Test
        fields = ("user_name", "user_email", "iso", "architecture",
                  "iso_type", "boot_type", "hardware_type",
                  "install_type", "source", "clock_choice", "filesystem",
                  "modules", "rollback_filesystem", "rollback_modules",
                  "bootloader", "success", "comments")
        widgets = {
            "modules": forms.CheckboxSelectMultiple(),
        }

def add_result(request):
    if request.POST:
        form = TestForm(request.POST)
        if form.is_valid() and request.POST['website'] == '':
            test = form.save(commit=False)
            test.ip_address = request.META.get("REMOTE_ADDR", None)
            test.save()
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

    context = {
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
            'iso_url': settings.ISO_LIST_URL,
    }
    return direct_to_template(request, 'isotests/results.html', context)

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

# vim: set ts=4 sw=4 et:
