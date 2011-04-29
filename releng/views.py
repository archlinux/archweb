from django import forms
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
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
    filesystem = standard_field(Filesystem,
            help_text="Check the installed system, including fstab.")
    modules = forms.ModelMultipleChoiceField(queryset=Module.objects.all(),
            help_text="", widget=forms.CheckboxSelectMultiple(), required=False)
    bootloader = standard_field(Bootloader)
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
                  "modules", "bootloader", "rollback_filesystem",
                  "rollback_modules", "success", "comments")
        widgets = {
            "modules": forms.CheckboxSelectMultiple(),
        }

def submit_test_result(request):
    if request.POST:
        form = TestForm(request.POST)
        if form.is_valid() and request.POST['website'] == '':
            test = form.save(commit=False)
            test.ip_address = request.META.get("REMOTE_ADDR", None)
            test.save()
            return redirect('releng-test-thanks')
    else:
        form = TestForm()

    context = {'form': form}
    return direct_to_template(request, 'releng/add.html', context)

def calculate_option_overview(model, is_rollback=False):
    option = {
        'option': model,
        'name': model._meta.verbose_name,
        'is_rollback': is_rollback,
        'values': []
    }
    for value in model.objects.all():
        data = { 'value': value }
        if is_rollback:
            data['success'] = value.get_last_rollback_success()
            data['failure'] = value.get_last_rollback_failure()
        else:
            data['success'] = value.get_last_success()
            data['failure'] = value.get_last_failure()
        option['values'].append(data)

    return option

def test_results_overview(request):
    # data structure produced:
    # [ { option, name, is_rollback, values: [ { value, success, failure } ... ] } ... ]
    all_options = []
    models = [ Architecture, IsoType, BootType, HardwareType, InstallType,
            Source, ClockChoice, Filesystem, Module, Bootloader ]
    for model in models:
        all_options.append(calculate_option_overview(model))
    # now handle rollback options
    for model in [ Filesystem, Module ]:
        all_options.append(calculate_option_overview(model, True))

    context = {
            'options': all_options,
            'iso_url': settings.ISO_LIST_URL,
    }
    return direct_to_template(request, 'releng/results.html', context)

def test_results_iso(request, iso_id):
    iso = get_object_or_404(Iso, pk=iso_id)
    test_list = iso.test_set.all()
    context = {
        'iso_name': iso.name,
        'test_list': test_list
    }
    return direct_to_template(request, 'releng/result_list.html', context)

def test_results_for(request, option, value):
    if option not in Test._meta.get_all_field_names():
        raise Http404
    option_model = getattr(Test, option).field.rel.to
    real_value = get_object_or_404(option_model, pk=value)
    test_list = real_value.test_set.order_by("iso__name", "pk")
    context = {
        'option': option,
        'value': real_value,
        'value_id': value,
        'test_list': test_list
    }
    return direct_to_template(request, 'releng/result_list.html', context)

def submit_test_thanks(request):
    return direct_to_template(request, "releng/thanks.html", None)

# vim: set ts=4 sw=4 et:
