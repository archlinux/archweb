from datetime import timedelta

import pytz
from django.db.models import F
from django.template.defaultfilters import filesizeformat
from django.db import connection
from django.utils.timezone import now
from main.models import Package, PackageFile, RebuilderdStatus
from packages.models import Depend, PackageRelation

from .models import DeveloperKey


class DeveloperReport(object):
    def __init__(self,
                 slug,
                 name,
                 desc,
                 packages_func,
                 names=None,
                 attrs=None,
                 personal=True):
        self.slug = slug
        self.name = name
        self.description = desc
        self.packages = packages_func
        self.names = names
        self.attrs = attrs
        self.personal = personal


def old(packages):
    cutoff = now() - timedelta(days=365 * 2)
    return packages.filter(build_date__lt=cutoff).order_by('build_date')


def outofdate(packages):
    cutoff = now() - timedelta(days=30)
    return packages.filter(flag_date__lt=cutoff).order_by('flag_date')


def big(packages):
    cutoff = 50 * 1024 * 1024
    packages = packages.filter(
        compressed_size__gte=cutoff).order_by('-compressed_size')
    # Format the compressed and installed sizes with MB/GB/etc suffixes
    for package in packages:
        package.compressed_size_pretty = filesizeformat(
            package.compressed_size)
        package.installed_size_pretty = filesizeformat(package.installed_size)
    return packages


def badcompression(packages):
    cutoff = 0.90 * F('installed_size')
    packages = packages.filter(
        compressed_size__gt=25 * 1024,
        installed_size__gt=25 * 1024,
        compressed_size__gte=cutoff).order_by('-compressed_size')

    # Format the compressed and installed sizes with MB/GB/etc suffixes
    for package in packages:
        package.compressed_size_pretty = filesizeformat(
            package.compressed_size)
        package.installed_size_pretty = filesizeformat(package.installed_size)
        ratio = package.compressed_size / float(package.installed_size)
        package.ratio = '%.3f' % ratio
        package.compress_type = package.filename.split('.')[-1]

    return packages


def uncompressed_man(packages, username):
    # checking for all '.0'...'.9' + '.n' extensions
    bad_files = PackageFile.objects.filter(
        is_directory=False,
        directory__contains='/man/',
        filename__regex=r'\.[0-9n]').exclude(filename__endswith='.gz').exclude(
            filename__endswith='.xz').exclude(
                filename__endswith='.bz2').exclude(filename__endswith='.html')
    if username:
        pkg_ids = set(packages.values_list('id', flat=True))
        bad_files = bad_files.filter(pkg__in=pkg_ids)
    bad_files = bad_files.values_list('pkg_id',
                                      flat=True).order_by().distinct()
    return packages.filter(id__in=set(bad_files))


def uncompressed_info(packages, username):
    # we don't worry about looking for '*.info-1', etc., given that an
    # uncompressed root page probably exists in the package anyway
    bad_files = PackageFile.objects.filter(is_directory=False,
                                           directory__endswith='/info/',
                                           filename__endswith='.info')
    if username:
        pkg_ids = set(packages.values_list('id', flat=True))
        bad_files = bad_files.filter(pkg__in=pkg_ids)
    bad_files = bad_files.values_list('pkg_id',
                                      flat=True).order_by().distinct()
    return packages.filter(id__in=set(bad_files))


def unneeded_orphans(packages):
    owned = PackageRelation.objects.all().values('pkgbase')
    required = Depend.objects.all().values('name')
    # The two separate calls to exclude is required to do the right thing
    return packages.exclude(pkgbase__in=owned).exclude(pkgname__in=required)


def mismatched_signature(packages):
    filtered = []
    packages = packages.select_related(
        'arch', 'repo', 'packager').filter(signature_bytes__isnull=False)
    known_keys = DeveloperKey.objects.select_related('owner').filter(
        owner__isnull=False)
    known_keys = {dk.key: dk for dk in known_keys}
    for package in packages:
        bad = False
        sig = package.signature
        dev_key = known_keys.get(sig.key_id, None)
        if dev_key:
            package.sig_by = dev_key.owner
            if dev_key.owner_id != package.packager_id:
                bad = True
        else:
            package.sig_by = sig.key_id
            bad = True

        if bad:
            filtered.append(package)
    return filtered


def signature_time(packages):
    cutoff = timedelta(hours=24)
    filtered = []
    packages = packages.select_related(
        'arch', 'repo', 'packager').filter(signature_bytes__isnull=False)
    for package in packages:
        sig = package.signature
        sig_date = sig.creation_time.replace(tzinfo=pytz.utc)
        package.sig_date = sig_date.date()
        if sig_date > package.build_date + cutoff:
            filtered.append(package)

    return filtered


def non_existing_dependencies(packages):
    cursor = connection.cursor()
    query = """
    select p.pkgname "pkgname", pd.name "dependency pkgname", depp.pkgname, provp.pkgname
    from packages_depend pd
    join packages p on p.id = pd.pkg_id
    left join packages depp on depp.pkgname = pd.name
    left join packages_provision depp_prov on depp_prov.name = pd.name
    left join packages provp on provp.id = depp_prov.pkg_id;"""

    packages = []
    cursor.execute(query)
    for row in cursor.fetchall():
        pkgname, pdname, dep_pkgname, prov_pkgname = row
        if not prov_pkgname and not dep_pkgname:
            package = Package.objects.normal().filter(pkgname=pkgname).first()
            package.nonexistingdep = pdname
            packages.append(package)

    return packages


def non_reproducible_packages(packages):
    statuses = RebuilderdStatus.objects.exclude(status=RebuilderdStatus.GOOD).values('pkg__pkgname')
    return packages.filter(pkgname__in=statuses)


REPORT_OLD = DeveloperReport(
    'old', 'Old', 'Packages last built more than two years ago', old)

REPORT_OUTOFDATE = DeveloperReport(
    'long-out-of-date', 'Long Out-of-date',
    'Packages marked out-of-date more than 30 days ago', outofdate)

REPORT_BIG = DeveloperReport(
    'big', 'Big', 'Packages with compressed size > 50 MiB', big,
    ['Compressed Size', 'Installed Size'],
    ['compressed_size_pretty', 'installed_size_pretty'])

REPORT_BADCOMPRESS = DeveloperReport(
    'badcompression', 'Bad Compression',
    'Packages > 25 KiB with a compression ratio < 10%', badcompression,
    ['Compressed Size', 'Installed Size', 'Ratio', 'Type'],
    ['compressed_size_pretty', 'installed_size_pretty', 'ratio',
     'compress_type'])

REPORT_MAN = DeveloperReport('uncompressed-man', 'Uncompressed Manpages',
                             'Packages with uncompressed manpages',
                             uncompressed_man)

REPORT_INFO = DeveloperReport('uncompressed-info', 'Uncompressed Info Pages',
                              'Packages with uncompressed info pages',
                              uncompressed_info)

REPORT_ORPHANS = DeveloperReport(
    'unneeded-orphans',
    'Unneeded Orphans',
    'Packages that have no maintainer and are not required by any ' +
    'other package in any repository',
    unneeded_orphans,
    personal=False)

REPORT_SIGNATURE = DeveloperReport(
    'mismatched-signature', 'Mismatched Signatures',
    'Packages where the signing key is unknown or signer != packager',
    mismatched_signature, ['Signed By', 'Packager'], ['sig_by', 'packager'])

REPORT_SIG_TIME = DeveloperReport(
    'signature-time', 'Signature Time',
    'Packages where the signature timestamp is more than 24 hours ' +
    'after the build timestamp', signature_time,
    ['Signature Date', 'Packager'], ['sig_date', 'packager'])

NON_EXISTING_DEPENDENCIES = DeveloperReport(
    'non-existing-dependencies',
    'Non existing dependencies',
    'Packages that have dependencies that do not exists in the repository',
    non_existing_dependencies,
    ['Non existing dependency'],
    ['nonexistingdep'],
    personal=False)

REBUILDERD_PACKAGES = DeveloperReport(
    'non-reproducible-packages',
    'Non Reproducible package',
    'Packages that are not reproducible on our reproducible.archlinux.org test environment',
    non_reproducible_packages,
    )


def available_reports():
    return (REPORT_OLD,
            REPORT_OUTOFDATE,
            REPORT_BIG,
            REPORT_BADCOMPRESS,
            REPORT_MAN,
            REPORT_INFO,
            REPORT_ORPHANS,
            REPORT_SIGNATURE,
            REPORT_SIG_TIME,
            NON_EXISTING_DEPENDENCIES,
            REBUILDERD_PACKAGES, )
