# -*- coding: utf-8 -*-
"""
reporead command

Parses a repo.db.tar.gz file and updates the Arch database with the relevant
changes.

Usage: ./manage.py reporead ARCH PATH
 ARCH:  architecture to update; must be available in the database
 PATH:  full path to the repo.db.tar.gz file.

Example:
  ./manage.py reporead i686 /tmp/core.db.tar.gz
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q

import io
import os
import re
import sys
import tarfile
import logging
from datetime import datetime
from optparse import make_option

from main.models import Arch, Package, PackageDepend, PackageFile, Repo
from packages.models import Conflict, Provision, Replacement

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-f', '--force', action='store_true', dest='force', default=False,
            help='Force a re-import of data for all packages instead of only new ones. Will not touch the \'last updated\' value.'),
        make_option('--filesonly', action='store_true', dest='filesonly', default=False,
            help='Load filelists if they are outdated, but will not add or remove any packages. Will not touch the \'last updated\' value.'),
    )
    help = "Runs a package repository import for the given arch and file."
    args = "<arch> <filename>"

    def handle(self, arch=None, filename=None, **options):
        if not arch:
            raise CommandError('Architecture is required.')
        if not validate_arch(arch):
            raise CommandError('Specified architecture %s is not currently known.' % arch)
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
        elif v == 2:
            logger.level = logging.DEBUG

        return read_repo(arch, filename, options)


class Pkg(object):
    """An interim 'container' object for holding Arch package data."""
    bare = ( 'name', 'base', 'arch', 'desc', 'filename',
            'md5sum', 'url', 'builddate', 'packager' )
    number = ( 'csize', 'isize' )
    collections = ( 'depends', 'optdepends', 'conflicts',
            'provides', 'replaces', 'groups', 'license', 'files' )

    version_re = re.compile(r'^((\d+):)?(.+)-([^-]+)$')

    def __init__(self, repo):
        self.repo = repo
        self.ver = None
        self.rel = None
        self.epoch = 0
        for k in self.bare + self.number:
            setattr(self, k, None)
        for k in self.collections:
            setattr(self, k, ())
        self.files = None
        self.has_files = False

    def populate(self, values):
        for k, v in values.iteritems():
            # ensure we stay under our DB character limit
            if k in self.bare:
                setattr(self, k, v[0][:254])
            elif k in self.number:
                setattr(self, k, long(v[0]))
            elif k == 'version':
                match = self.version_re.match(v[0])
                self.ver = match.group(3)
                self.rel = match.group(4)
                if match.group(2):
                    self.epoch = int(match.group(2))
            elif k == 'files':
                self.files = v
                self.has_files = True
            else:
                # anything left in collections
                setattr(self, k, v)

    @property
    def full_version(self):
        '''Very similar to the main.models.Package method.'''
        if self.epoch > 0:
            return u'%d:%s-%s' % (self.epoch, self.ver, self.rel)
        return u'%s-%s' % (self.ver, self.rel)


def find_user(userstring):
    '''
    Attempt to find the corresponding User object for a standard
    packager string, e.g. something like
        'A. U. Thor <author@example.com>'.
    We start by searching for a matching email address; we then move onto
    matching by first/last name. If we cannot find a user, then return None.
    '''
    if userstring in find_user.cache:
        return find_user.cache[userstring]
    matches = re.match(r'^([^<]+)? ?<([^>]*)>', userstring)
    if not matches:
        return None

    user = None
    name = matches.group(1)
    email = matches.group(2)

    def user_email():
        return User.objects.get(email=email)
    def profile_email():
        return User.objects.get(userprofile__public_email=email)
    def user_name():
        # yes, a bit odd but this is the easiest way since we can't always be
        # sure how to split the name. Ensure every 'token' appears in at least
        # one of the two name fields.
        name_q = Q()
        for token in name.split():
            # ignore quoted parts; e.g. nicknames in strings
            if re.match(r'^[\'"].*[\'"]$', token):
                continue
            name_q &= (Q(first_name__icontains=token) |
                    Q(last_name__icontains=token))
        return User.objects.get(name_q)

    for matcher in (user_email, profile_email, user_name):
        try:
            user = matcher()
            break
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            pass

    find_user.cache[userstring] = user
    return user

# cached mappings of user strings -> User objects so we don't have to do the
# lookup more than strictly necessary.
find_user.cache = {}

DEPEND_RE = re.compile(r"^(.+?)((>=|<=|=|>|<)(.*))?$")

def create_depend(package, dep_str, optional=False):
    depend = PackageDepend(pkg=package, optional=optional)
    # lop off any description first
    parts = dep_str.split(':', 1)
    if len(parts) > 1:
        depend.description = parts[1].strip()
    match = DEPEND_RE.match(parts[0].strip())
    if match:
        depend.depname = match.group(1)
        if match.group(2):
            depend.depvcmp = match.group(2)
    else:
        logger.warning('Package %s had unparsable depend string %s',
                package.pkgname, dep_str)
        return None
    depend.save(force_insert=True)
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
    related.save(force_insert=True)
    return related

def create_multivalued(dbpkg, repopkg, db_attr, repo_attr):
    '''Populate the simplest of multivalued attributes. These are those that
    only deal with a 'name' attribute, such as licenses, groups, etc. The input
    and output objects and attribute names are specified, and everything is
    done via getattr().'''
    collection = getattr(dbpkg, db_attr)
    collection.all().delete()
    for name in getattr(repopkg, repo_attr):
        collection.create(name=name)

def populate_pkg(dbpkg, repopkg, force=False, timestamp=None):
    db_score = 1

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
    try:
        dbpkg.build_date = datetime.utcfromtimestamp(int(repopkg.builddate))
    except ValueError:
        try:
            dbpkg.build_date = datetime.strptime(repopkg.builddate,
                    '%a %b %d %H:%M:%S %Y')
        except ValueError:
            logger.warning('Package %s had unparsable build date %s',
                    repopkg.name, repopkg.builddate)
    dbpkg.packager_str = repopkg.packager
    # attempt to find the corresponding django user for this string
    dbpkg.packager = find_user(repopkg.packager)

    if timestamp:
        dbpkg.flag_date = None
        dbpkg.last_update = timestamp
    dbpkg.save()

    db_score += populate_files(dbpkg, repopkg, force=force)

    dbpkg.packagedepend_set.all().delete()
    for y in repopkg.depends:
        create_depend(dbpkg, y)
    for y in repopkg.optdepends:
        create_depend(dbpkg, y, True)

    dbpkg.conflicts.all().delete()
    for y in repopkg.conflicts:
        create_related(Conflict, dbpkg, y)
    dbpkg.provides.all().delete()
    for y in repopkg.provides:
        create_related(Provision, dbpkg, y, equals_only=True)
    dbpkg.replaces.all().delete()
    for y in repopkg.replaces:
        create_related(Replacement, dbpkg, y)

    create_multivalued(dbpkg, repopkg, 'groups', 'groups')
    create_multivalued(dbpkg, repopkg, 'licenses', 'license')

    related_score = (len(repopkg.depends) + len(repopkg.optdepends)
            + len(repopkg.conflicts) + len(repopkg.provides)
            + len(repopkg.replaces) + len(repopkg.groups)
            + len(repopkg.license))
    if related_score:
        db_score += (related_score / 20) + 1

    return db_score


def populate_files(dbpkg, repopkg, force=False):
    if not force:
        if dbpkg.pkgver != repopkg.ver or dbpkg.pkgrel != repopkg.rel \
                or dbpkg.epoch != repopkg.epoch:
            logger.info("DB version (%s) didn't match repo version "
                    "(%s) for package %s, skipping file list addition",
                    dbpkg.full_version, repopkg.full_version, dbpkg.pkgname)
            return 0
        if not dbpkg.files_last_update or not dbpkg.last_update:
            pass
        elif dbpkg.files_last_update > dbpkg.last_update:
            return 0
    # only delete files if we are reading a DB that contains them
    if repopkg.has_files:
        dbpkg.packagefile_set.all().delete()
        logger.info("adding %d files for package %s",
                len(repopkg.files), dbpkg.pkgname)
        for f in repopkg.files:
            dirname, filename = f.rsplit('/', 1)
            if filename == '':
                filename = None
            # this is basically like calling dbpkg.packagefile_set.create(),
            # but much faster as we can skip a lot of the repeated code paths
            pkgfile = PackageFile(pkg=dbpkg,
                    is_directory=(filename is None),
                    directory=dirname + '/',
                    filename=filename)
            pkgfile.save(force_insert=True)
        dbpkg.files_last_update = datetime.utcnow()
        dbpkg.save()
        return (len(repopkg.files) / 50) + 1
    return 0


class Batcher(object):
    def __init__(self, threshold, start=0):
        self.threshold = threshold
        self.meter = start

    def batch_commit(self, score):
        """
        Track updates to the database and perform a commit if the batch
        becomes sufficiently large. "Large" is defined by waiting for the
        sum of scores to exceed the arbitrary threshold value; once it is
        hit a commit is issued.
        """
        self.meter += score
        if self.meter > self.threshold:
            logger.debug("Committing transaction, batch threshold hit")
            transaction.commit()
            self.meter = 0


@transaction.commit_on_success
def db_update(archname, reponame, pkgs, options):
    """
    Parses a list and updates the Arch dev database accordingly.

    Arguments:
      pkgs -- A list of Pkg objects.

    """
    logger.info('Updating Arch: %s', archname)
    force = options.get('force', False)
    filesonly = options.get('filesonly', False)
    repository = Repo.objects.get(name__iexact=reponame)
    architecture = Arch.objects.get(name__iexact=archname)
    # no-arg order_by() removes even the default ordering; we don't need it
    dbpkgs = Package.objects.filter(
            arch=architecture, repo=repository).order_by()
    # This makes our inner loop where we find packages by name *way* more
    # efficient by not having to go to the database for each package to
    # SELECT them by name.
    dbdict = dict([(pkg.pkgname, pkg) for pkg in dbpkgs])

    logger.debug("Creating sets")
    dbset = set(dbdict.keys())
    syncset = set([pkg.name for pkg in pkgs])
    logger.info("%d packages in current web DB", len(dbset))
    logger.info("%d packages in new updating db", len(syncset))
    in_sync_not_db = syncset - dbset
    logger.info("%d packages in sync not db", len(in_sync_not_db))

    # Try to catch those random package deletions that make Eric so unhappy.
    if len(dbset):
        dbpercent = 100.0 * len(syncset) / len(dbset)
    else:
        dbpercent = 0.0
    logger.info("DB package ratio: %.1f%%", dbpercent)

    # Fewer than 20 packages makes the percentage check unreliable, but it also
    # means we expect the repo to fluctuate a lot.
    msg = "Package database has %.1f%% the number of packages in the " \
            "web database" % dbpercent
    if len(dbset) == 0 and len(syncset) == 0:
        pass
    elif not filesonly and \
            len(dbset) > 20 and dbpercent < 50.0 and \
            not repository.testing and not repository.staging:
        logger.error(msg)
        raise Exception(msg)
    elif dbpercent < 75.0:
        logger.warning(msg)

    batcher = Batcher(100)

    if not filesonly:
        # packages in syncdb and not in database (add to database)
        for p in [x for x in pkgs if x.name in in_sync_not_db]:
            logger.info("Adding package %s", p.name)
            pkg = Package(pkgname = p.name, arch = architecture, repo = repository)
            score = populate_pkg(pkg, p, timestamp=datetime.utcnow())
            batcher.batch_commit(score)

        # packages in database and not in syncdb (remove from database)
        in_db_not_sync = dbset - syncset
        for p in in_db_not_sync:
            logger.info("Removing package %s", p)
            dbp = dbdict[p]
            dbp.delete()
            batcher.batch_commit(score)

    # packages in both database and in syncdb (update in database)
    pkg_in_both = syncset & dbset
    for p in [x for x in pkgs if x.name in pkg_in_both]:
        logger.debug("Looking for package updates")
        dbp = dbdict[p.name]
        timestamp = None
        # for a force, we don't want to update the timestamp.
        # for a non-force, we don't want to do anything at all.
        if filesonly:
            pass
        elif p.ver == dbp.pkgver and p.rel == dbp.pkgrel \
                and p.epoch == dbp.epoch:
            if not force:
                continue
        else:
            timestamp = datetime.utcnow()

        if filesonly:
            logger.debug("Checking files for package %s", p.name)
            score = populate_files(dbp, p, force=force)
        else:
            logger.info("Updating package %s", p.name)
            score = populate_pkg(dbp, p, force=force, timestamp=timestamp)

        batcher.batch_commit(score)

    logger.info('Finished updating Arch: %s', archname)


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
            logger.debug("Parsing package block %s", blockname)
            store[blockname] = []
        elif blockname:
            store[blockname].append(line)
        else:
            raise Exception("Read package info outside a block: %s" % line)
    return store


def parse_repo(repopath):
    """
    Parses an Arch repo db file, and returns a list of Pkg objects.

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
    dbfiles = ('desc', 'depends', 'files')
    pkgs = {}
    for tarinfo in repodb.getmembers():
        if tarinfo.isreg():
            pkgid, fname = os.path.split(tarinfo.name)
            if fname not in dbfiles:
                continue
            data_file = repodb.extractfile(tarinfo)
            data_file = io.TextIOWrapper(io.BytesIO(data_file.read()),
                    encoding='utf=8')
            try:
                data = parse_info(data_file)
                p = pkgs.setdefault(pkgid, Pkg(reponame))
                p.populate(data)
            except UnicodeDecodeError:
                logger.warn("Could not correctly decode %s, skipping file",
                        tarinfo.name)
            data_file.close()

            logger.debug("Done parsing file %s", fname)

    repodb.close()
    logger.info("Finished repo parsing, %d total packages", len(pkgs))
    return (reponame, pkgs.values())

def validate_arch(archname):
    "Check if arch is valid."
    return Arch.objects.filter(name__iexact=archname).exists()

def read_repo(primary_arch, repo_file, options):
    """
    Parses repo.db.tar.gz file and returns exit status.
    """
    repo, packages = parse_repo(repo_file)

    # group packages by arch -- to handle noarch stuff
    packages_arches = {}
    for arch in Arch.objects.filter(agnostic=True):
        packages_arches[arch.name] = []
    packages_arches[primary_arch] = []

    for package in packages:
        if package.arch in packages_arches:
            packages_arches[package.arch].append(package)
        else:
            # we don't include mis-arched packages
            logger.warning("Package %s arch = %s",
                package.name,package.arch)
    logger.info('Starting database updates.')
    for arch in sorted(packages_arches.keys()):
        db_update(arch, repo, packages_arches[arch], options)
    logger.info('Finished database updates.')
    return 0

# vim: set ts=4 sw=4 et:
