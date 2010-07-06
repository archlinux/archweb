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

# multi value blocks
REPOVARS = ['arch', 'backup', 'base', 'builddate', 'conflicts', 'csize',
            'deltas', 'depends', 'desc', 'filename', 'files', 'force',
            'groups', 'installdate', 'isize', 'license', 'md5sum',
            'name', 'optdepends', 'packager', 'provides', 'reason',
            'replaces', 'size', 'url', 'version']


from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models, transaction
from django.core import management

import os
import re
import sys
import tarfile
import logging
from datetime import datetime
from optparse import make_option

from cStringIO import StringIO
from logging import ERROR, WARNING, INFO, DEBUG

from main.models import Arch, Package, Repo

class SomethingFishyException(Exception):
    '''Raised when the database looks like its going to wipe out a bunch of
    packages.'''
    pass

logging.basicConfig(
    level=WARNING,
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

    def handle(self, arch=None, file=None, **options):
        if not arch:
            raise CommandError('Architecture is required.')
        if not validate_arch(arch):
            raise CommandError('Specified architecture %s is not currently known.' % arch)
        if not file:
            raise CommandError('Package database file is required.')
        file = os.path.normpath(file)
        if not os.path.exists(file) or not os.path.isfile(file):
            raise CommandError('Specified package database file does not exist.')

        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = ERROR
        elif v == 1:
            logger.level = INFO
        elif v == 2:
            logger.level = DEBUG

        return read_repo(arch, file, options)


class Pkg(object):
    """An interim 'container' object for holding Arch package data."""

    def __init__(self, val):
        selfdict = {}
        squash = ['arch', 'builddate', 'csize', 'desc', 'filename',
                  'installdate', 'isize', 'license', 'md5sum',
                  'packager', 'size', 'url']

        selfdict['name'] = val['name'][0]
        selfdict['base'] = None
        del val['name']
        if 'license' not in val:
            val['license'] = []
        for x in val.keys():
            if x in squash:
                if val[x] == None or len(val[x]) == 0:
                    logger.warning("Package %s has no %s" % (selfdict['name'],x))
                    selfdict[x] = None
                else:
                    selfdict[x] = ', '.join(val[x])
                    # make sure we don't have elements larger than the db char
                    # fields
                    if len(selfdict[x]) > 255:
                        selfdict[x] = selfdict[x][:254]
            elif x == 'base':
                selfdict[x] = val[x][0]
            elif x == 'force':
                selfdict[x] = True
            elif x == 'version':
                version = val[x][0].rsplit('-')
                selfdict['ver'] = version[0]
                selfdict['rel'] = version[1]
            elif x == 'reason':
                selfdict[x] = int(val[x][0])
            else:
                selfdict[x] = val[x]
        self.__dict__ = selfdict

    def __getattr__(self,name):
        if name == 'force':
            return False
        else:
            return None


def populate_pkg(dbpkg, repopkg, force=False, timestamp=None):
    if repopkg.base:
        dbpkg.pkgbase = repopkg.base
    else:
        dbpkg.pkgbase = repopkg.name
    dbpkg.pkgver = repopkg.ver
    dbpkg.pkgrel = repopkg.rel
    dbpkg.pkgdesc = repopkg.desc
    dbpkg.license = repopkg.license
    dbpkg.url = repopkg.url
    dbpkg.filename = repopkg.filename
    dbpkg.compressed_size = int(repopkg.csize)
    dbpkg.installed_size = int(repopkg.isize)
    try:
        dbpkg.build_date = datetime.utcfromtimestamp(int(repopkg.builddate))
    except:
        try:
            dbpkg.build_date = datetime.strptime(repopkg.builddate, '%a %b %d %H:%M:%S %Y')
        except:
            pass

    if timestamp:
        dbpkg.flag_date = None
        dbpkg.last_update = timestamp
    dbpkg.save()

    populate_files(dbpkg, repopkg, force=force)

    dbpkg.packagedepend_set.all().delete()
    if 'depends' in repopkg.__dict__:
        for y in repopkg.depends:
            # make sure we aren't adding self depends..
            # yes *sigh* i have seen them in pkgbuilds
            dpname,dpvcmp = re.match(r"([a-z0-9._+-]+)(.*)", y).groups()
            if dpname == repopkg.name:
                logger.warning('Package %s has a depend on itself' % repopkg.name)
                continue
            dbpkg.packagedepend_set.create(depname=dpname, depvcmp=dpvcmp)
            logger.debug('Added %s as dep for pkg %s' % (dpname,repopkg.name))

def populate_files(dbpkg, repopkg, force=False):
    if not force:
        if not dbpkg.files_last_update or not dbpkg.last_update:
            pass
        elif dbpkg.files_last_update > dbpkg.last_update:
            return
    # only delete files if we are reading a DB that contains them
    if 'files' in repopkg.__dict__:
        dbpkg.packagefile_set.all().delete()
        logger.info("adding %d files for package %s" % (len(repopkg.files), dbpkg.pkgname))
        for x in repopkg.files:
            dbpkg.packagefile_set.create(path=x)
        dbpkg.files_last_update = datetime.now()
        dbpkg.save()

def db_update(archname, reponame, pkgs, options):
    """
    Parses a list and updates the Arch dev database accordingly.

    Arguments:
      pkgs -- A list of Pkg objects.

    """
    logger.info('Updating Arch: %s' % archname)
    force = options.get('force', False)
    filesonly = options.get('filesonly', False)
    repository = Repo.objects.get(name__iexact=reponame)
    architecture = Arch.objects.get(name__iexact=archname)
    dbpkgs = Package.objects.filter(arch=architecture, repo=repository)
    # It makes sense to fully evaluate our DB query now because we will
    # be using 99% of the objects in our "in both sets" loop. Force eval
    # by calling list() on the QuerySet.
    list(dbpkgs)
    # This makes our inner loop where we find packages by name *way* more
    # efficient by not having to go to the database for each package to
    # SELECT them by name.
    dbdict = dict([(pkg.pkgname, pkg) for pkg in dbpkgs])

    # go go set theory!
    # thank you python for having a set class <3
    logger.debug("Creating sets")
    dbset = set([pkg.pkgname for pkg in dbpkgs])
    syncset = set([pkg.name for pkg in pkgs])
    logger.info("%d packages in current web DB" % len(dbset))
    logger.info("%d packages in new updating db" % len(syncset))
    # packages in syncdb and not in database (add to database)
    logger.debug("Set theory: Packages in syncdb not in database")
    in_sync_not_db = syncset - dbset
    logger.info("%d packages in sync not db" % len(in_sync_not_db))

    # Try to catch those random orphaning issues that make Eric so unhappy.
    if len(dbset) > 20:
        dbpercent = 100.0 * len(syncset) / len(dbset)
    else:
        # we don't have 20 packages in this repo/arch, so this check could
        # produce a lot of false positives (or a div by zero). fake it
        dbpercent = 100.0
    logger.info("DB package ratio: %.1f%%" % dbpercent)
    if dbpercent < 50.0 and not repository.testing:
        logger.error(".db.tar.gz has %.1f%% the number of packages in the web database" % dbpercent)
        raise SomethingFishyException(
            'It looks like the syncdb is less than half the size of the web db. WTF?')

    if dbpercent < 75.0:
        logger.warning(".db.tar.gz has %.1f%% the number of packages in the web database." % dbpercent)

    if not filesonly:
        # packages in syncdb and not in database (add to database)
        logger.debug("Set theory: Packages in syncdb not in database")
        for p in [x for x in pkgs if x.name in in_sync_not_db]:
            logger.info("Adding package %s", p.name)
            pkg = Package(pkgname = p.name, arch = architecture, repo = repository)
            populate_pkg(pkg, p, timestamp=datetime.now())

        # packages in database and not in syncdb (remove from database)
        logger.debug("Set theory: Packages in database not in syncdb")
        in_db_not_sync = dbset - syncset
        for p in in_db_not_sync:
            logger.info("Removing package %s from database", p)
            Package.objects.get(
                pkgname=p, arch=architecture, repo=repository).delete()

    # packages in both database and in syncdb (update in database)
    logger.debug("Set theory: Packages in database and syncdb")
    pkg_in_both = syncset & dbset
    for p in [x for x in pkgs if x.name in pkg_in_both]:
        logger.debug("Looking for package updates")
        dbp = dbdict[p.name]
        timestamp = None
        # for a force, we don't want to update the timestamp.
        # for a non-force, we don't want to do anything at all.
        if filesonly:
            pass
        elif ''.join((p.ver,p.rel)) == ''.join((dbp.pkgver,dbp.pkgrel)):
            if not force:
                continue
        else:
            timestamp = datetime.now()
        if filesonly:
            logger.debug("Checking files for package %s in database", p.name)
            populate_files(dbp, p)
        else:
            logger.info("Updating package %s in database", p.name)
            populate_pkg(dbp, p, force=force, timestamp=timestamp)

    logger.info('Finished updating Arch: %s' % archname)


def parse_inf(iofile):
    """
    Parses an Arch repo db information file, and returns variables as a list.

    Arguments:
     iofile -- A StringIO, FileType, or other object with readlines method.

    """
    store = {}
    lines = iofile.readlines()
    blockname = None
    max = len(lines)
    i = 0
    while i < max:
        line = lines[i].strip()
        if len(line) > 0 and line[0] == '%' and line[1:-1].lower() in REPOVARS:
            blockname = line[1:-1].lower()
            logger.debug("Parsing package block %s",blockname)
            store[blockname] = []
            i += 1
            while i < max and len(lines[i].strip()) > 0:
                store[blockname].append(lines[i].strip())
                i += 1
            # here is where i would convert arrays to strings
            # based on count and type, but i dont think it is needed now
        i += 1

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
    m = re.match(r"^(.*)\.(db|files)\.tar\.(.*)$", filename)
    if m:
        reponame = m.group(1)
    else:
        logger.error("File does not have the proper extension")
        raise SomethingFishyException("File does not have the proper extension")

    repodb = tarfile.open(repopath,"r:gz")
    ## assuming well formed tar, with dir first then files after
    ## repo-add enforces this
    logger.debug("Starting package parsing")
    dbfiles = ('desc', 'depends', 'files')
    pkgs = []
    tpkg = None
    while True:
        tarinfo = repodb.next()
        if tarinfo == None or tarinfo.isdir():
            if tpkg != None:
                tpkg.reset()
                data = parse_inf(tpkg)
                p = Pkg(data)
                p.repo = reponame
                logger.debug("Done parsing package %s", p.name)
                pkgs.append(p)
            if tarinfo == None:
                break
            # set new tpkg
            tpkg = StringIO()
        if tarinfo.isreg():
            fname = os.path.split(tarinfo.name)[1]
            if fname in dbfiles:
                tpkg.write(repodb.extractfile(tarinfo).read())
                tpkg.write('\n') # just in case
    repodb.close()
    logger.info("Finished repo parsing")
    return (reponame, pkgs)

def validate_arch(arch):
    "Check if arch is valid."
    available_arches = [x.name for x in Arch.objects.all()]
    return arch in available_arches

@transaction.commit_on_success
def read_repo(primary_arch, file, options):
    """
    Parses repo.db.tar.gz file and returns exit status.
    """
    repo, packages = parse_repo(file)

    # sort packages by arch -- to handle noarch stuff
    packages_arches = {}
    packages_arches['any'] = []
    packages_arches[primary_arch] = []

    for package in packages:
        if package.arch in ('any', primary_arch):
            packages_arches[package.arch].append(package)
        else:
            # we don't include mis-arched packages
            logger.warning("Package %s arch = %s" % (
                package.name,package.arch))
    logger.info('Starting database updates.')
    for (arch, pkgs) in packages_arches.items():
        db_update(arch, repo, pkgs, options)
    logger.info('Finished database updates.')
    return 0

# vim: set ts=4 sw=4 et:
