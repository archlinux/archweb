"""
reposec command

Parses all packages in a given repo and creates PackageSecurity
objects which check for PIE, RELRO, Stack Canary's and Fortify.

Usage: ./manage.py reposec ARCH PATH
 ARCH:  architecture to check
 PATH:  full path to the repository directory.

Example:
  ./manage.py reposec x86_64 /srv/ftp/core
"""

import io
import os
import re
import sys
import logging

from glob import glob
from multiprocessing import Pool, cpu_count

from elftools.elf.constants import P_FLAGS
from elftools.elf.dynamic import DynamicSection
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from libarchive import file_reader

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from main.models import Arch, Package, PackageSecurity, Repo


PKG_EXT = '.tar.xz' # TODO: detect zstd..
BIN_PATHS = ['usr/bin/', 'opt/']
STACK_CHK = set(["__stack_chk_fail", "__stack_smash_handler"])


logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
TRACE = 5
logging.addLevelName(TRACE, 'TRACE')
logger = logging.getLogger()

class Command(BaseCommand):
    help = "Checks all packages in the repository for missing hardening bits (relro, stack canary, pie, etc)"
    missing_args_message = 'missing arch and file.'

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*', help='<arch> <filename>')
        parser.add_argument('--processes',
                            action='store_true',
                            dest='processes',
                            default=cpu_count(),
                            help=f'number of parallel processes (default: {cpu_count()})')


    def handle(self, arch=None, directory=None, processes=cpu_count(), **options):
        if not arch:
            raise CommandError('Architecture is required.')
        if not directory:
            raise CommandError('Repo location is required.')
        directory = os.path.normpath(directory)
        if not os.path.exists(directory):
            raise CommandError('Specified repository location does not exists.')

        v = int(options.get('verbosity', 0))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v >= 2:
            logger.level = logging.DEBUG

        return read_repo(arch, directory, processes, options)


def read_file(filename):
    '''
    Read a pacman package and determine the 'package security status' by
    finding all ELF files and determining the worst status of all ELF files in
    the repo.
    '''

    elffiles = []
    
    with file_reader(filename) as pkg:
        pkgname = os.path.basename(filename).rsplit('-', 3)[0]

        for entry in pkg:
            if not entry.isfile:
                continue

            if not any(entry.name.startswith(path) for path in BIN_PATHS):
                continue

            fp = io.BytesIO(b''.join(entry.get_blocks()))
            elf = Elf(entry.name, fp)

            if not elf.is_elf():
                continue

            if elf.hardened:
                continue

            data = elf.dump()
            data['pkgname'] = pkgname
            elffiles.append(data)

    return elffiles


def read_repo(arch, source_dir, processes, options):
    tasks = []

    directory = os.path.join(source_dir, 'os', arch)
    for filename in glob(os.path.join(directory, f'*{PKG_EXT}')):
        tasks.append((filename))

    arch = Arch.objects.get(name=arch)

    reponame = os.path.basename(source_dir).title()
    repo = Repo.objects.get(name=reponame)

    packagesecs = []

    with Pool(processes=processes) as pool:
        for results in pool.imap_unordered(read_file, tasks):
            # No elf files
            if not results:
                continue

            # determine 
            print(results)
            for result in results:
                try:
                    pkg = Package.objects.get(pkgname=result['pkgname'], arch=arch, repo=repo)
                except Exception:
                    print("package '%s' not found in repo" % result['pkgname'])
                    continue

                print(result)
                packagesec = PackageSecurity(pkg=pkg, relro=result['relro'],
                                             pie=result['pie'], canary=result['canary'],
                                             filename=result['filename'])
                packagesecs.append(packagesec)

    print(packagesecs)
    with transaction.atomic():
        PackageSecurity.objects.bulk_create(packagesecs)


class Elf:
    def __init__(self, filename, fileobj):
        self.filename = filename
        self.fileobj = fileobj
        self._elffile = None

    @property
    def elffile(self):
        if not self._elffile:
            self._elffile = ELFFile(self.fileobj)
        return self._elffile

    def is_elf(self): 
        "Take file object, peek at the magic bytes to check if ELF file."
        magic_bytes = b"\x7fELF"
        length = len(magic_bytes)
        magic = self.fileobj.read(length)
        self.fileobj.seek(0)
        return magic == magic_bytes

    def dynamic_tags(self, key):
        for section in self.elffile.iter_sections():
            if not isinstance(section, DynamicSection):
                continue
            for tag in section.iter_tags():
                if tag.entry.d_tag == key:
                    return tag
        return None

    @property
    def rpath(self, key="DT_RPATH", verbose=False):
        tag = self.dynamic_tags(key)
        if tag and verbose:
            return tag.rpath
        if tag:
            return 'RPATH'
        return ''

    @property
    def runpath(self, key="DT_RUNPATH", verbose=False):
        tag = self.dynamic_tags(key)
        if tag and verbose:
            return tag.runpath
        if tag:
            return 'RUNPATH'

        return ''

    @property
    def relro(self):
        if self.elffile.num_segments() == 0:
            return PackageSecurity.NO_RELRO

        have_relro = PackageSecurity.NO_RELRO
        for segment in self.elffile.iter_segments():
            if re.search("GNU_RELRO", str(segment['p_type'])):
                have_relro = PackageSecurity.FULL_RELRO
                break

        if self.dynamic_tags("DT_BIND_NOW") and have_relro:
            return PackageSecurity.FULL_RELRO
        if have_relro: # partial
            return PackageSecurity.PARTIAL_RELRO
        return PackageSecurity.FULL_RELRO

    @property
    def pie(self):
        header = self.elffile.header
        if self.dynamic_tags("EXEC"):
            return False
        if "ET_DYN" in header['e_type']:
            if self.dynamic_tags("DT_DEBUG"):
                return True
            return True # DSO is PIE
        return False

    @property
    def canary(self):
        for section in self.elffile.iter_sections():
            if not isinstance(section, SymbolTableSection):
                continue
            if section['sh_entsize'] == 0:
                continue
            for _, symbol in enumerate(section.iter_symbols()):
                if symbol.name in STACK_CHK:
                    return True
        return False

    @property
    def hardened(self):
        return self.pie and self.canary and self.relro == PackageSecurity.FULL_RELRO

    def dump(self):
        return {
                'pie': self.pie,
                'relro': self.relro,
                'canary': self.canary,
                'filename': self.filename
        }
