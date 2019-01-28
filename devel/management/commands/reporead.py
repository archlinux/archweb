# -*- coding: utf-8 -*-
"""
reporead command

Parses a repo.db.tar.gz file and updates the Arch database with the relevant
changes.

Usage: ./manage.py reporead ARCH PATH
 ARCH:  architecture to update; must be available in the database
 PATH:  full path to the repo.db.tar.gz file.

Example:
  ./manage.py reporead x86_64 /tmp/core.db.tar.gz
"""

from base64 import b64decode
from collections import defaultdict
from copy import copy
import io
import os
import re
import sys
import tarfile
import logging
from datetime import datetime
from pytz import utc

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, router, transaction
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.contrib.auth.models import User

from devel.utils import UserFinder
from main.models import Arch, Package, PackageFile, Repo
from packages.models import Depend, Conflict, FlagRequest, Provision, Replacement, Update, PackageRelation
from packages.utils import parse_version


logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
TRACE = 5
logging.addLevelName(TRACE, 'TRACE')
logger = logging.getLogger()

class Command(BaseCommand):
    help = "Runs a package repository import for the given arch and file."
    missing_args_message = 'missing arch and file.'

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*', help='<arch> <filename>')
        parser.add_argument('--force',
                            action='store_true',
                            dest='force',
                            default=False,
                            help='Force a re-import of data for all packages instead of only new ones. Will not touch the \'last updated\' value.')

        parser.add_argument('--filesonly',
                            action='store_true',
                            dest='filesonly',
                            default=False,
                            help='Load filelists if they are outdated, but will not add or remove any packages. Will not touch the \'last updated\' value.')

    def handle(self, arch=None, filename=None, **options):
        if not arch:
            raise CommandError('Architecture is required.')
        if not filename:
            raise CommandError('Package database file is required.')
        filename = os.path.normpath(filename)
        if not os.path.exists(filename) or not os.path.isfile(filename):
            raise CommandError('Specified package database file does not exist.')

        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        return read_repo(arch, filename, options)


class RepoPackage(object):
    """An interim 'container' object for holding Arch package data."""
    bare = ( 'name', 'base', 'arch', 'filename',
            'md5sum', 'sha256sum', 'url', 'packager' )
    number = ( 'csize', 'isize' )
    collections = ( 'depends', 'optdepends', 'makedepends', 'checkdepends',
            'conflicts', 'provides', 'replaces', 'groups', 'license')

    def __init__(self, repo):
        self.repo = repo
        self.ver = None
        self.rel = None
        self.epoch = 0
        self.desc = None
        self.pgpsig = None
        for k in self.bare + self.number:
            setattr(self, k, None)
        for k in self.collections:
            setattr(self, k, ())
        self.builddate = None
        self.files = None

    def populate(self, values):
        for k, v in values.items():
            # ensure we stay under our DB character limit
            if k in self.bare:
                setattr(self, k, v[0][:254])
            elif k in self.number:
                setattr(self, k, int(v[0]))
            elif k in ('desc', 'pgpsig'):
                # do NOT prune these values at all
                setattr(self, k, v[0])
            elif k == 'version':
                self.ver, self.rel, self.epoch = parse_version(v[0])
            elif k == 'builddate':
                try:
                    builddate = datetime.utcfromtimestamp(int(v[0]))
                    self.builddate = builddate.replace(tzinfo=utc)
                except ValueError:
                    logger.warning(
                            'Package %s had unparsable build date %s',
                            self.name, v[0])
            else:
                # anything left in collections
                setattr(self, k, tuple(v))

    @property
    def files_list(self):
        data_file = io.TextIOWrapper(io.BytesIO(self.files), encoding='UTF-8')
        try:
            info = parse_info(data_file)
        except UnicodeDecodeError:
            logger.warning("Could not correctly decode files list for %s",
                    self.name)
            return None
        return info['files']

    @property
    def full_version(self):
        '''Very similar to the main.models.Package method.'''
        if self.epoch > 0:
            return '%d:%s-%s' % (self.epoch, self.ver, self.rel)
        return '%s-%s' % (self.ver, self.rel)


DEPEND_RE = re.compile(r"^(.+?)((>=|<=|=|>|<)(.+))?$")

def create_depend(package, dep_str, deptype='D'):
    depend = Depend(pkg=package, deptype=deptype)
    # lop off any description first, don't get confused by epoch
    parts = dep_str.split(': ', 1)
    if len(parts) > 1:
        depend.description = parts[1].strip()
    match = DEPEND_RE.match(parts[0].strip())
    if match:
        depend.name = match.group(1)
        if match.group(3):
            depend.comparison = match.group(3)
        if match.group(4):
            depend.version = match.group(4)
    else:
        logger.warning('Package %s had unparsable depend string %s',
                package.pkgname, dep_str)
        return None
    return depend

def create_related(model, package, rel_str, equals_only=False):
    related = model(pkg=package)
    match = DEPEND_RE.match(rel_str)
    if match:
        related.name = match.group(1)
        if match.group(3):
            comp = match.group(3)
            if not equals_only:
                related.comparison = comp
            elif comp != '=':
                logger.warning(
                        'Package %s had unexpected comparison operator %s for %s in %s',
                        package.pkgname, comp, model.__name__, rel_str)
        if match.group(4):
            related.version = match.group(4)
    else:
        logger.warning('Package %s had unparsable %s string %s',
                package.pkgname, model.___name__, rel_str)
        return None
    return related


def create_multivalued(dbpkg, repopkg, db_attr, repo_attr):
    '''Populate the simplest of multivalued attributes. These are those that
    only deal with a 'name' attribute, such as licenses, groups, etc. The input
    and output objects and attribute names are specified, and everything is
    done via getattr().'''
    collection = getattr(dbpkg, db_attr)
    collection.all().delete()
    model = collection.model
    new_items = []
    for name in getattr(repopkg, repo_attr):
        new_items.append(model(pkg=dbpkg, name=name))
    if new_items:
        model.objects.bulk_create(new_items)

finder = UserFinder()

def populate_pkg(dbpkg, repopkg, force=False, timestamp=None):
    # we reset the flag date only if the upstream version components change;
    # e.g. epoch or pkgver, but not pkgrel
    if dbpkg.epoch is None or dbpkg.epoch != repopkg.epoch:
        dbpkg.flag_date = None
    elif dbpkg.pkgver is None or dbpkg.pkgver != repopkg.ver:
        dbpkg.flag_date = None

    # Remove flagged out of date objects when a package is updated.
    if dbpkg.epoch != repopkg.epoch or dbpkg.pkgver != repopkg.ver:
        repo = Repo.objects.get(name__iexact=repopkg.repo)
        requests = FlagRequest.objects.filter(pkgbase=repopkg.base, repo=repo)
        requests = requests.exclude(pkgver=repopkg.ver, epoch=repopkg.epoch)
        requests.delete()

    if repopkg.base:
        dbpkg.pkgbase = repopkg.base
    else:
        dbpkg.pkgbase = repopkg.name
    dbpkg.pkgver = repopkg.ver
    dbpkg.pkgrel = repopkg.rel
    dbpkg.epoch = repopkg.epoch
    dbpkg.pkgdesc = repopkg.desc
    dbpkg.url = repopkg.url
    dbpkg.filename = repopkg.filename
    dbpkg.compressed_size = repopkg.csize
    dbpkg.installed_size = repopkg.isize
    dbpkg.build_date = repopkg.builddate
    dbpkg.packager_str = repopkg.packager
    # attempt to find the corresponding django user for this string
    dbpkg.packager = finder.find(repopkg.packager)
    dbpkg.signature_bytes = b64decode(repopkg.pgpsig.encode('utf-8'))

    if timestamp:
        dbpkg.last_update = timestamp
    dbpkg.save()

    populate_files(dbpkg, repopkg, force=force)

    dbpkg.depends.all().delete()
    deps = [create_depend(dbpkg, y) for y in repopkg.depends]
    deps += [create_depend(dbpkg, y, 'O') for y in repopkg.optdepends]
    deps += [create_depend(dbpkg, y, 'M') for y in repopkg.makedepends]
    deps += [create_depend(dbpkg, y, 'C') for y in repopkg.checkdepends]
    Depend.objects.bulk_create(deps)

    dbpkg.conflicts.all().delete()
    conflicts = [create_related(Conflict, dbpkg, y) for y in repopkg.conflicts]
    Conflict.objects.bulk_create(conflicts)

    dbpkg.provides.all().delete()
    provides = [create_related(Provision, dbpkg, y, equals_only=True)
            for y in repopkg.provides]
    Provision.objects.bulk_create(provides)

    dbpkg.replaces.all().delete()
    replaces = [create_related(Replacement, dbpkg, y) for y in repopkg.replaces]
    Replacement.objects.bulk_create(replaces)

    create_multivalued(dbpkg, repopkg, 'groups', 'groups')
    create_multivalued(dbpkg, repopkg, 'licenses', 'license')


pkg_same_version = lambda pkg, dbpkg: pkg.ver == dbpkg.pkgver \
        and pkg.rel == dbpkg.pkgrel and pkg.epoch == dbpkg.epoch


def delete_pkg_files(dbpkg):
    database = router.db_for_write(Package, instance=dbpkg)
    cursor = connections[database].cursor()
    cursor.execute('DELETE FROM package_files WHERE pkg_id = %s', [dbpkg.id])


def batched_bulk_create(model, all_objects):
    cutoff = 10000
    length = len(all_objects)
    if length < cutoff:
        return model.objects.bulk_create(all_objects)

    def chunks():
        offset = 0
        while offset < length:
            yield all_objects[offset:offset + cutoff]
            offset += cutoff

    for items in chunks():
        ret = model.objects.bulk_create(items)

    return ret


def populate_files(dbpkg, repopkg, force=False):
    if not force:
        if not pkg_same_version(repopkg, dbpkg):
            logger.info("DB version (%s) didn't match repo version "
                    "(%s) for package %s, skipping file list addition",
                    dbpkg.full_version, repopkg.full_version, dbpkg.pkgname)
            return
        if not dbpkg.files_last_update or not dbpkg.last_update:
            pass
        elif dbpkg.files_last_update >= dbpkg.last_update:
            return

    # only delete files if we are reading a DB that contains them
    if repopkg.files:
        files = repopkg.files_list
        # we had files data, but it couldn't be parsed, so skip
        if not files:
            return
        delete_pkg_files(dbpkg)
        logger.info("adding %d files for package %s",
                len(files), dbpkg.pkgname)
        pkg_files = []
        # sort in normal alpha-order that pacman uses, rather than makepkg's
        # default breadth-first, directory-first ordering
        for f in sorted(files):
            if '/' in f:
                dirname, filename = f.rsplit('/', 1)
                dirname += '/'
            else:
                dirname, filename = '', f
            if filename == '':
                filename = None
            pkgfile = PackageFile(pkg=dbpkg,
                    is_directory=(filename is None),
                    directory=dirname,
                    filename=filename)
            pkg_files.append(pkgfile)
        batched_bulk_create(PackageFile, pkg_files)
        dbpkg.files_last_update = now()
        dbpkg.save()


def update_common(archname, reponame, pkgs, sanity_check=True):
    # If isolation level is repeatable-read, we need to ensure each package
    # update starts a new transaction and re-queries the database as
    # necessary to guard against simultaneous updates.
    with transaction.atomic():
        # force the transaction dirty, even though we will only do reads
        # https://github.com/django/django/blob/3c447b108ac70757001171f7a4791f493880bf5b/docs/releases/1.3.txt#L606
        #transaction.set_dirty()

        repository = Repo.objects.get(name__iexact=reponame)
        architecture = Arch.objects.get(name=archname)
        # no-arg order_by() removes even the default ordering; we don't need it
        dbpkgs = Package.objects.filter(
                arch=architecture, repo=repository).order_by()

        logger.info("%d packages in current web DB", len(dbpkgs))
        logger.info("%d packages in new updating DB", len(pkgs))

        if len(dbpkgs):
            dbpercent = 100.0 * len(pkgs) / len(dbpkgs)
        else:
            dbpercent = 0.0
        logger.info("DB package ratio: %.1f%%", dbpercent)

        # Fewer than 20 packages makes the percentage check unreliable, but it
        # also means we expect the repo to fluctuate a lot.
        msg = "Package database %s (%s) has %.1f%% the number of packages " \
                "the web database"
        if not sanity_check:
            pass
        elif repository.testing or repository.staging:
            pass
        elif len(dbpkgs) == 0 and len(pkgs) == 0:
            pass
        elif len(dbpkgs) > 20 and dbpercent < 50.0:
            logger.error(msg, reponame, archname, dbpercent)
            raise Exception(msg % (reponame, archname, dbpercent))
        elif dbpercent < 75.0:
            logger.warning(msg, reponame, archname, dbpercent)

    return dbpkgs

def db_update(archname, reponame, pkgs, force=False):
    """
    Parses a list of packages and updates the packages database accordingly.
    """
    logger.info('Updating %s (%s)', reponame, archname)
    dbpkgs = update_common(archname, reponame, pkgs, True)
    repository = Repo.objects.get(name__iexact=reponame)
    architecture = Arch.objects.get(name=archname)

    # This makes our inner loop where we find packages by name *way* more
    # efficient by not having to go to the database for each package to
    # SELECT them by name.
    dbdict = {dbpkg.pkgname: dbpkg for dbpkg in dbpkgs}

    dbset = set(dbdict.keys())
    syncset = {pkg.name for pkg in pkgs}

    in_sync_not_db = syncset - dbset
    logger.info("%d packages in sync not db", len(in_sync_not_db))
    # packages in syncdb and not in database (add to database)
    for pkg in (pkg for pkg in pkgs if pkg.name in in_sync_not_db):
        logger.info("Adding package %s", pkg.name)
        timestamp = now()
        dbpkg = Package(pkgname=pkg.name, arch=architecture, repo=repository,
                created=timestamp)
        try:
            with transaction.atomic():
                populate_pkg(dbpkg, pkg, timestamp=timestamp)
                Update.objects.log_update(None, dbpkg)

                if not Package.objects.filter(
                        pkgname=pkg.name).exclude(id=dbpkg.id).exists():
                    if not User.objects.filter(
                            package_relations__pkgbase=dbpkg.pkgbase,
                            package_relations__type=PackageRelation.MAINTAINER
                            ).exists():
                        packager = finder.find(pkg.packager)
                        if packager:
                            prel = PackageRelation(pkgbase=dbpkg.pkgbase,
                                                   user=packager,
                                                   type=PackageRelation.MAINTAINER)
                            prel.save()


        except IntegrityError:
            if architecture.agnostic:
                logger.warning("Could not add package %s; "
                        "not fatal if another thread beat us to it.",
                        pkg.name)
            else:
                logger.exception("Could not add package %s", pkg.name)

    # packages in database and not in syncdb (remove from database)
    for pkgname in (dbset - syncset):
        logger.info("Removing package %s", pkgname)
        dbpkg = dbdict[pkgname]
        with transaction.atomic():
            Update.objects.log_update(dbpkg, None)
            # no race condition here as long as simultaneous threads both
            # issue deletes; second delete will be a no-op
            delete_pkg_files(dbpkg)
            dbpkg.delete()

    # packages in both database and in syncdb (update in database)
    pkg_in_both = syncset & dbset
    for pkg in (x for x in pkgs if x.name in pkg_in_both):
        logger.debug("Checking package %s", pkg.name)
        dbpkg = dbdict[pkg.name]
        timestamp = None
        # for a force, we don't want to update the timestamp.
        # for a non-force, we don't want to do anything at all.
        if not force and pkg_same_version(pkg, dbpkg):
            continue
        elif not force:
            timestamp = now()

        # The odd select_for_update song and dance here are to ensure
        # simultaneous updates don't happen on a package, causing
        # files/depends/all related items to be double-imported.
        with transaction.atomic():
            dbpkg = Package.objects.select_for_update().get(id=dbpkg.id)
            if not force and pkg_same_version(pkg, dbpkg):
                logger.debug("Package %s was already updated", pkg.name)
                continue
            logger.info("Updating package %s", pkg.name)
            prevpkg = copy(dbpkg)
            populate_pkg(dbpkg, pkg, force=force, timestamp=timestamp)
            Update.objects.log_update(prevpkg, dbpkg)

    logger.info('Finished updating arch: %s', archname)


def filesonly_update(archname, reponame, pkgs, force=False):
    """
    Parses a list of packages and updates the packages database accordingly.
    """
    logger.info('Updating files for %s (%s)', reponame, archname)
    dbpkgs = update_common(archname, reponame, pkgs, False)
    dbdict = {dbpkg.pkgname: dbpkg for dbpkg in dbpkgs}
    dbset = set(dbdict.keys())

    for pkg in (pkg for pkg in pkgs if pkg.name in dbset):
        dbpkg = dbdict[pkg.name]

        # The odd select_for_update song and dance here are to ensure
        # simultaneous updates don't happen on a package, causing
        # files to be double-imported.
        with transaction.atomic():
            if not dbpkg.files_last_update or not dbpkg.last_update:
                pass
            elif not force and dbpkg.files_last_update >= dbpkg.last_update:
                logger.debug("Files for %s are up to date", pkg.name)
                continue
            dbpkg = Package.objects.select_for_update().get(id=dbpkg.id)
            logger.debug("Checking files for package %s", pkg.name)
            populate_files(dbpkg, pkg, force=force)

    logger.info('Finished updating arch: %s', archname)


def parse_info(iofile):
    """
    Parses an Arch repo db information file, and returns variables as a list.
    """
    store = {}
    blockname = None
    for line in iofile:
        line = line.strip()
        if len(line) == 0:
            continue
        elif line.startswith('%') and line.endswith('%'):
            blockname = line[1:-1].lower()
            logger.log(TRACE, "Parsing package block %s", blockname)
            store[blockname] = []
        elif blockname:
            store[blockname].append(line)
        else:
            raise Exception("Read package info outside a block: %s" % line)
    return store


def parse_repo(repopath):
    """
    Parses an Arch repo db file, and returns a list of RepoPackage objects.

    Arguments:
     repopath -- The path of a repository db file.

    """
    logger.info("Starting repo parsing")
    if not os.path.exists(repopath):
        logger.error("Could not read file %s", repopath)

    logger.info("Reading repo tarfile %s", repopath)
    filename = os.path.split(repopath)[1]
    m = re.match(r"^(.*)\.(db|files)\.tar(\..*)?$", filename)
    if m:
        reponame = m.group(1)
    else:
        logger.error("File does not have the proper extension")
        raise Exception("File does not have the proper extension")

    repodb = tarfile.open(repopath, "r")
    logger.debug("Starting package parsing")
    newpkg = lambda: RepoPackage(reponame)
    pkgs = defaultdict(newpkg)
    for tarinfo in repodb.getmembers():
        if tarinfo.isreg():
            pkgid, fname = os.path.split(tarinfo.name)
            if fname == 'files':
                # don't parse yet for speed and memory consumption reasons
                files_data = repodb.extractfile(tarinfo)
                pkgs[pkgid].files = files_data.read()
                del files_data
            elif fname in ('desc', 'depends'):
                data_file = repodb.extractfile(tarinfo)
                data_file = io.TextIOWrapper(io.BytesIO(data_file.read()),
                        encoding='UTF-8')
                try:
                    pkgs[pkgid].populate(parse_info(data_file))
                except UnicodeDecodeError:
                    logger.warning("Could not correctly decode %s, skipping file",
                            tarinfo.name)
                data_file.close()
                del data_file

            logger.debug("Done parsing file %s/%s", pkgid, fname)

    repodb.close()
    logger.info("Finished repo parsing, %d total packages", len(pkgs))
    return (reponame, list(pkgs.values()))

def locate_arch(arch):
    "Check if arch is valid."
    if isinstance(arch, Arch):
        return arch
    try:
        return Arch.objects.get(name=arch)
    except Arch.DoesNotExist:
        raise CommandError(
                'Specified architecture %s is not currently known.' % arch)


def read_repo(primary_arch, repo_file, options):
    """
    Parses repo.db.tar.gz file and returns exit status.
    """
    # always returns an Arch object, regardless of what is passed in
    primary_arch = locate_arch(primary_arch)
    force = options.get('force', False)
    filesonly = options.get('filesonly', False)

    repo, packages = parse_repo(repo_file)

    # group packages by arch -- to handle noarch stuff
    packages_arches = {}
    for arch in Arch.objects.filter(agnostic=True):
        packages_arches[arch.name] = []
    packages_arches[primary_arch.name] = []

    for package in packages:
        if package.arch in packages_arches:
            packages_arches[package.arch].append(package)
        else:
            raise Exception(
                    "Package %s in database %s had wrong architecture %s" % (
                    package.name, repo_file, package.arch))
    del packages

    database = router.db_for_write(Package)
    connection = connections[database]
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA synchronous = NORMAL')

    logger.info('Starting database updates for %s.', repo_file)
    for arch in sorted(packages_arches.keys()):
        if filesonly:
            filesonly_update(arch, repo, packages_arches[arch], force)
        else:
            db_update(arch, repo, packages_arches[arch], force)
    logger.info('Finished database updates for %s.', repo_file)
    connection.commit()
    connection.close()
    return 0

# vim: set ts=4 sw=4 et:
