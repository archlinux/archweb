#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
reporead.py

Parses a repo.db.tar.gz file and updates the Arch database with the relevant
changes.

Usage: reporead.py ARCH PATH
 ARCH:  architecture to update, and can be one of: i686, x86_64
 PATH:  full path to the repo.db.tar.gz file.

Example:
  reporead.py i686 /tmp/core.db.tar.gz

"""

###
### User Variables
###

# multi value blocks
REPOVARS = ['arch', 'backup', 'base', 'builddate', 'conflicts', 'csize',
            'deltas', 'depends', 'desc', 'filename', 'files', 'force', 
            'groups', 'installdate', 'isize', 'license', 'md5sum', 
            'name', 'optdepends', 'packager', 'provides', 'reason', 
            'replaces', 'size', 'url', 'version']

###
### Imports
###

import os
import re
import sys
import tarfile
import logging
from datetime import datetime
from django.core.management import setup_environ
# mung the sys path to get to django root dir, no matter
# where we are called from
# TODO this is so fricking ugly
archweb_app_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
os.chdir(archweb_app_path)
sys.path[0] = archweb_app_path
import settings
setup_environ(settings)
# the transaction import must be below where we set up our db stuff...
from django.db import transaction
from cStringIO import StringIO
from logging import WARNING,INFO,DEBUG
from main.models import Arch, Package, Repo

class SomethingFishyException(Exception):
    '''Raised when the database looks like its going to wipe out a bunch of
    packages.'''
    pass

###
### Initialization
###

logging.basicConfig(
    level=WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


###
### function and class definitions
###

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
        if 'desc' not in val:
            logger.warning("Package %s has no description" % selfdict['name'])
            val['desc'] = ''
        if 'url' not in val:
            val['url'] = ''
        if 'license' not in val:
            val['license'] = []
        for x in val.keys():
            if x in squash:
                if len(val[x]) == 0:
                    logger.warning("Package %s has no %s" % (selfdict['name'],x))
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


def usage():
    """Print the usage of this application."""
    print __doc__.strip()


def fetchiter_dict(cursor):
    """
    Given a DB API 2.0 cursor object that has been executed, returns a 
    dictionary that maps each field to a column index
    """
    rows = cursor.fetchmany(size=30)
    while rows:
        for row in rows:
            #pp(rows)
            #for row in rows:
            yield dictize(cursor,row)
        rows = cursor.fetchmany(size=30)


def fetchone_dict(cursor):
    """
    Given a DB API 2.0 cursor object that has been executed, returns a 
    dictionary that maps each field to a column index
    """
    results = {}
    row = cursor.fetchone()
    return dictize(cursor,row)


def dictize(cursor,row):
    result = {}
    for column,desc in enumerate(cursor.description):
        result[desc[0]] = row[column]
    return result


def populate_pkg(dbpkg, repopkg, timestamp=None):
    if not timestamp: timestamp = datetime.now()
    dbpkg.pkgbase = repopkg.base
    dbpkg.pkgver = repopkg.ver
    dbpkg.pkgrel = repopkg.rel
    dbpkg.pkgdesc = repopkg.desc
    dbpkg.license = repopkg.license
    dbpkg.url = repopkg.url
    dbpkg.needupdate = False
    dbpkg.last_update = timestamp
    dbpkg.save()
    # files are not in the repo.db.tar.gz
    #for x in repopkg.files:
    #    dbpkg.packagefile_set.create(path=x)
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


def db_update(archname, pkgs):
    """
    Parses a list and updates the Arch dev database accordingly.

    Arguments:
      pkgs -- A list of Pkg objects.
    
    """
    logger.info('Updating Arch: %s' % archname)
    repository = Repo.objects.get(name__iexact=pkgs[0].repo)
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
    now = datetime.now()

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
    if dbpercent < 50.0 and repository.name.lower().find('testing') == -1:
        logger.error(".db.tar.gz has %.1f%% the number of packages in the web database" % dbpercent)
        raise SomethingFishyException(
            'It looks like the syncdb is less than half the size of the web db. WTF?')

    if dbpercent < 75.0:
        logger.warning(".db.tar.gz has %.1f%% the number of packages in the web database." % dbpercent)
    
    for p in [x for x in pkgs if x.name in in_sync_not_db]:
        logger.info("Adding package %s", p.name)
        pkg = Package(pkgname = p.name, arch = architecture, repo = repository)
        populate_pkg(pkg, p, timestamp=now)

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
        if ''.join((p.ver,p.rel)) == ''.join((dbp.pkgver,dbp.pkgrel)):
            continue
        logger.info("Updating package %s in database", p.name)
        pkg = Package.objects.get(
            pkgname=p.name,arch=architecture, repo=repository)
        populate_pkg(pkg, p, timestamp=now)

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
    rindex = filename.rindex('.db.tar.gz')
    reponame = filename[:rindex]
    
    repodb = tarfile.open(repopath,"r:gz")
    ## assuming well formed tar, with dir first then files after
    ## repo-add enforces this
    logger.debug("Starting package parsing")
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
            if os.path.split(tarinfo.name)[1] in ('desc','depends'):
                tpkg.write(repodb.extractfile(tarinfo).read())
                tpkg.write('\n') # just in case 
    repodb.close()
    logger.info("Finished repo parsing")
    return pkgs


@transaction.commit_on_success
def main(argv=None):
    """
    Parses repo.db.tar.gz file and returns exit status.

    Keyword Arguments:
     argv -- A list/array simulating a sys.argv (default None)
             If left empty, sys.argv is used

    """
    if argv == None:
        argv = sys.argv
    if len(argv) != 3:
        usage()
        return 0
    # check if arch is valid
    available_arches = [x.name for x in Arch.objects.all()]
    if argv[1] not in available_arches:
        usage()
        return 0
    else:
        primary_arch = argv[1]

    repo_file = os.path.normpath(argv[2])
    packages = parse_repo(repo_file)
    
    # sort packages by arch -- to handle noarch stuff
    packages_arches = {}
    for arch in available_arches:
        packages_arches[arch] = []
    
    for package in packages:
        if package.arch in ('any', primary_arch):
            packages_arches[package.arch].append(package)
        else:
            logger.warning("Package %s arch = %s" % (
                package.name,package.arch))
            #package.arch = primary_arch


    logger.info('Starting database updates.')
    for (arch, pkgs) in packages_arches.iteritems():
        if len(pkgs) > 0:
            db_update(arch,pkgs)
    logger.info('Finished database updates.')
    return 0


###
### Main eval 
###

if __name__ == '__main__':
    logger.level = INFO
    sys.exit(main())

