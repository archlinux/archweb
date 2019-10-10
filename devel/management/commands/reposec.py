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

from functools import partial
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


PKG_EXT = '.tar.xz'
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
    help = ""
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

    pkgsec = {}
    elffiles = []
    
    with file_reader(filename) as pkg:
        for entry in pkg:
            if not entry.isfile:
                continue

            if not entry.name.startswith('usr/bin/'):
                continue

            fp = io.BytesIO(b''.join(entry.get_blocks()))
            elf = Elf(fp)

            if not elf.is_elf():
                continue

            elffiles.append(elf)

            
    if elffiles:
        elf = elffiles[0]
        print(elffiles)
    
    yield pkgsec



def read_repo(arch, source_dir, processes, options):
    tasks = []

    directory = os.path.join(source_dir, 'os', arch)
    for filename in glob(os.path.join(directory, f'*{PKG_EXT}')):
        tasks.append((filename))

    arch = Arch.objects.get(name=arch)

    reponame = os.path.basename(source_dir).title()
    repo = Repo.objects.get(name=reponame)


    with Pool(processes=processes) as pool:
        results = pool.imap(read_file, tasks)

    # Process and add Package object.
    results = [r for r in results if r]
    resutls = [r for r in results if not r.pie or not r.relro or not r.canary]

    print(results)
    return

    with transaction.atomic():
        PackageSecurity.objects.all().delete()
        PackageSecurity.objects.bulk_create(results)


class Elf:
    def __init__(self, fileobj):
        self.fileobj = fileobj
        self._elffile = None

    @property
    def elffile(self):
        if not self._elffile:
            self._elffile = ELFFile(self.fileobj)
        return self._elffile

    def _file_has_magic(self, fileobj, magic_bytes):
        length = len(magic_bytes)
        magic = fileobj.read(length)
        fileobj.seek(0)
        return magic == magic_bytes

    def is_elf(self):
        "Take file object, peek at the magic bytes to check if ELF file."
        return self._file_has_magic(self.fileobj, b"\x7fELF")

    def dynamic_tags(self, key):
        for section in self.elffile.iter_sections():
            if not isinstance(section, DynamicSection):
                continue
            for tag in section.iter_tags():
                if tag.entry.d_tag == key:
                    return tag
        return None

    def rpath(self, key="DT_RPATH", verbose=False):
        tag = self.dynamic_tags(key)
        if tag and verbose:
            return tag.rpath
        if tag:
            return 'RPATH'
        return ''

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
            return "Disabled"

        have_relro = False
        for segment in self.elffile.iter_segments():
            if re.search("GNU_RELRO", str(segment['p_type'])):
                have_relro = True
                break

        if self.dynamic_tags("DT_BIND_NOW") and have_relro:
            return True
        if have_relro: # partial
            return False
        return False

    @property
    def pie(self):
        header = self.elffile.header
        if self.dynamic_tags("EXEC"):
            return "Disabled"
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

    def program_headers(self):
        pflags = P_FLAGS()
        if self.elffile.num_segments() == 0:
            return ""

        found = False
        for segment in self.elffile.iter_segments():
            if search("GNU_STACK", str(segment['p_type'])):
                found = True
                if segment['p_flags'] & pflags.PF_X:
                    return "Disabled"
        if found:
            return "Enabled"
        return "Disabled"
