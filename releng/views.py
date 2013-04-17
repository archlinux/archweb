from base64 import b64decode

from django import forms
from django.conf import settings
from django.db.models import Count, Max
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from .models import (Architecture, BootType, Bootloader, ClockChoice,
        Filesystem, HardwareType, InstallType, Iso, IsoType, Module, Source,
        Test, Release)


def standard_field(model, empty_label=None, help_text=None, required=True):
    return forms.ModelChoiceField(queryset=model.objects.all(),
        widget=forms.RadioSelect(), empty_label=empty_label,
        help_text=help_text, required=required)


class TestForm(forms.ModelForm):
    iso = forms.ModelChoiceField(queryset=Iso.objects.filter(
        active=True).order_by('-id'))
    architecture = standard_field(Architecture)
    iso_type = standard_field(IsoType)
    boot_type = standard_field(BootType)
    hardware_type = standard_field(HardwareType)
    install_type = standard_field(InstallType)
    source = standard_field(Source)
    clock_choice = standard_field(ClockChoice)
    filesystem = standard_field(Filesystem,
            help_text="Verify /etc/fstab, `df -hT` output and commands like "
            "lvdisplay for special modules.")
    modules = forms.ModelMultipleChoiceField(queryset=Module.objects.all(),
            widget=forms.CheckboxSelectMultiple(), required=False)
    bootloader = standard_field(Bootloader,
            help_text="Verify that the entries in the bootloader config "
            "looks OK.")
    rollback_filesystem = standard_field(Filesystem,
            help_text="If you did a rollback followed by a new attempt to "
            "setup your blockdevices/filesystems, select which option you "
            "took here.",
            empty_label="N/A (did not rollback)", required=False)
    rollback_modules = forms.ModelMultipleChoiceField(
            queryset=Module.objects.all(),
            help_text="If you did a rollback followed by a new attempt to "
            "setup your blockdevices/filesystems, select which option you "
            "took here.",
            widget=forms.CheckboxSelectMultiple(), required=False)
    success = forms.BooleanField(
            help_text="Only check this if everything went fine. "
            "If you ran into problems please create a ticket on <a "
            "href=\"https://bugs.archlinux.org/index.php?project=6\">the "
            "bugtracker</a> (or check that one already exists) and link to "
            "it in the comments.",
            required=False)
    website = forms.CharField(label='',
            widget=forms.TextInput(attrs={'style': 'display:none;'}),
            required=False)

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
            form.save_m2m()
            return redirect('releng-test-thanks')
    else:
        form = TestForm()

    context = {'form': form}
    return render(request, 'releng/add.html', context)


def calculate_option_overview(field_name):
    field = Test._meta.get_field(field_name)
    model = field.rel.to
    is_rollback = field_name.startswith('rollback_')
    option = {
        'option': model,
        'field_name': field_name,
        'name': model._meta.verbose_name,
        'is_rollback': is_rollback,
        'values': []
    }
    if not is_rollback:
        successes = dict(model.objects.values_list('pk').filter(
            test__success=True).annotate(latest=Max('test__iso__id')))
        failures = dict(model.objects.values_list('pk').filter(
            test__success=False).annotate(latest=Max('test__iso__id')))
    else:
        successes = dict(model.objects.values_list('pk').filter(
            rollback_test_set__success=True).annotate(
                latest=Max('rollback_test_set__iso__id')))
        failures = dict(model.objects.values_list('pk').filter(
            rollback_test_set__success=False).annotate(
                latest=Max('rollback_test_set__iso__id')))

    for value in model.objects.all():
        data = {
            'value': value,
            'success': successes.get(value.pk),
            'failure': failures.get(value.pk),
        }
        option['values'].append(data)

    return option


def options_fetch_iso(options):
    '''Replaces the Iso PK with a full Iso model object in a list of options
    used on the overview page. We do it this way to only have to query the Iso
    table once rather than once per option.'''
    # collect all necessary Iso PKs
    all_pks = set()
    for option in options:
        all_pks.update(v['success'] for v in option['values'])
        all_pks.update(v['failure'] for v in option['values'])

    all_pks.discard(None)
    all_isos = Iso.objects.in_bulk(all_pks)

    for option in options:
        for value in option['values']:
            value['success'] = all_isos.get(value['success'])
            value['failure'] = all_isos.get(value['failure'])

    return options


def test_results_overview(request):
    # data structure produced:
    # [ {
    #     option, name, is_rollback,
    #     values: [ { value, success, failure } ... ]
    #   }
    #   ...
    # ]
    all_options = []
    fields = ['architecture', 'iso_type', 'boot_type', 'hardware_type',
            'install_type', 'source', 'clock_choice', 'filesystem', 'modules',
            'bootloader', 'rollback_filesystem', 'rollback_modules']
    for field in fields:
        all_options.append(calculate_option_overview(field))

    all_options = options_fetch_iso(all_options)

    context = {
            'options': all_options,
            'iso_url': settings.ISO_LIST_URL,
    }
    return render(request, 'releng/results.html', context)


def test_results_iso(request, iso_id):
    iso = get_object_or_404(Iso, pk=iso_id)
    test_list = iso.test_set.select_related()
    context = {
        'iso_name': iso.name,
        'test_list': test_list
    }
    return render(request, 'releng/result_list.html', context)


def test_results_for(request, option, value):
    if option not in Test._meta.get_all_field_names():
        raise Http404
    option_model = getattr(Test, option).field.rel.to
    option_model.verbose_name = option_model._meta.verbose_name
    real_value = get_object_or_404(option_model, pk=value)
    test_list = real_value.test_set.select_related().order_by(
            '-iso__name', '-pk')
    context = {
        'option': option_model,
        'value': real_value,
        'value_id': value,
        'test_list': test_list
    }
    return render(request, 'releng/result_list.html', context)


def submit_test_thanks(request):
    return render(request, "releng/thanks.html", None)


def iso_overview(request):
    isos = Iso.objects.all().order_by('-pk')
    successes = dict(Iso.objects.values_list('pk').filter(
        test__success=True).annotate(ct=Count('test')))
    failures = dict(Iso.objects.values_list('pk').filter(
        test__success=False).annotate(ct=Count('test')))
    for iso in isos:
        iso.successes = successes.get(iso.pk, 0)
        iso.failures = failures.get(iso.pk, 0)

    # only show "useful" rows, currently active ISOs or those with results
    isos = [iso for iso in isos if
            iso.active is True or iso.successes > 0 or iso.failures > 0]

    context = {
        'isos': isos
    }
    return render(request, 'releng/iso_overview.html', context)


class ReleaseListView(ListView):
    model = Release


class ReleaseDetailView(DetailView):
    model = Release
    slug_field = 'version'
    slug_url_kwarg = 'version'


def release_torrent(request, version):
    release = get_object_or_404(Release, version=version)
    if not release.torrent_data:
        raise Http404
    data = b64decode(release.torrent_data.encode('utf-8'))
    response = HttpResponse(data, content_type='application/x-bittorrent')
    # TODO: this is duplicated from Release.iso_url()
    filename = 'archlinux-%s-dual.iso.torrent' % release.version
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

# vim: set ts=4 sw=4 et:
