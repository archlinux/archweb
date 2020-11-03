import logging
import os
import re
import sys
import tarfile

from django.core.management.base import BaseCommand, CommandError

from main.models import Repo, Package, Soname


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()


class Command(BaseCommand):
    help = "Import links db (soname mapping)."
    missing_args_message = 'missing links db'

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*', help='<arch> <filename>')

    def handle(self, filename=None, **options):
        if not filename:
            raise CommandError('Links database file is required.')

        filename = os.path.normpath(filename)
        if not os.path.exists(filename) or not os.path.isfile(filename):
            raise CommandError('Specified links database file does not exist.')

        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        return read_linksdb(filename)


def get_pkginfo(pkgnamever):
    pkgname, pkgver, pkgrel = pkgnamever.rsplit('-', 2)
    epoch = '0'
    if ':' in pkgver:
        epoch, pkgver = pkgver.split(':')

    return pkgname, epoch, pkgver, pkgrel


def read_linksdb(repopath):
    logger.info("Starting linksdb parsing")
    if not os.path.exists(repopath):
        logger.error("Could not read file %s", repopath)

    logger.info("Reading repo tarfile %s", repopath)
    filename = os.path.split(repopath)[1]
    m = re.match(r"^(.*)\.links\.tar(\..*)?$", filename)
    if m:
        reponame = m.group(1)
    else:
        logger.error("File does not have the proper extension")
        raise Exception("File does not have the proper extension")

    repository = Repo.objects.get(name__iexact=reponame)
    sonames = []

    with tarfile.open(repopath, 'r') as repodb:
        logger.debug("Starting soname parsing")

        for tarinfo in repodb.getmembers():
            if tarinfo.isreg():
                pkgnamever = os.path.dirname(tarinfo.name)
                pkgnamever = pkgnamever.replace('./', '')
                pkgname, epoch, pkgver, pkgrel = get_pkginfo(pkgnamever)

                dbpkg = Package.objects.filter(pkgname=pkgname, pkgver=pkgver,
                                               pkgrel=pkgrel, epoch=epoch,
                                               repo=repository).first()

                if not dbpkg:
                    logging.info("Package name '%s' not found in repo database", pkgname)
                    continue

                files_data = repodb.extractfile(tarinfo)
                old_sonames = Soname.objects.filter(pkg=dbpkg)
                for soname in files_data:
                    soname = soname.strip().decode()
                    # New soname which we do not track yet for this package
                    if not old_sonames.filter(name=soname):
                        sonames.append(Soname(pkg=dbpkg, name=soname))

    if sonames:
        Soname.objects.bulk_create(sonames)
