# Archweb README

[![Actions Status](https://github.com/archlinux/archweb/workflows/Github-Actions/badge.svg)](https://github.com/archlinux/archweb/actions)
[![Build Status](https://travis-ci.com/archlinux/archweb.svg?branch=master)](https://travis-ci.com/archlinux/archweb)
[![Coverage Status](https://coveralls.io/repos/github/archlinux/archweb/badge.svg?branch=master)](https://coveralls.io/github/archlinux/archweb?branch=master)

To get a pretty version of this document, run

    $ markdown README > README.html

# License

See LICENSE file.

# Authors

See AUTHORS file.

# Dependencies

- python
- rsync (optional for mirrorcheck with rsync mirrors)

# Python dependencies

More detail in `requirements.txt` and `requirements_prod.txt`; it is best to
use virtualenv and pip to handle these. But if you insist on (Arch Linux)
packages, you will probably want the following:

- python-django
- python-psycopg2
- python-markdown
- python-memcached

# Testing Installation

1. Run `python -m venv env`.

        cd /path/to/archweb && python -m venv ./env/

2. Activate the virtualenv.

        source ./env/bin/activate

2. Install dependencies through `pip`.

        pip install -r requirements.txt

3. Copy `local_settings.py.example` to `local_settings.py` and modify.
   Make sure to uncomment the appropriate database section (either sqlite or
   PostgreSQL).

4. Migrate changes.

        ./manage.py migrate

5. Load the fixtures to pre populate some data. If you don't want some of the
   provided data, adjust the file glob accordingly.

        ./manage.py loaddata main/fixtures/*.json
        ./manage.py loaddata devel/fixtures/*.json
        ./manage.py loaddata mirrors/fixtures/*.json
        ./manage.py loaddata releng/fixtures/*.json

6. Use the following commands to start a service instance

        ./manage.py runserver

7. To optionally populate the database with real data:

        wget http://mirrors.kernel.org/archlinux/core/os/x86_64/core.db.tar.gz
        ./manage.py reporead x86_64 core.db.tar.gz
        # Package file listing
        wget http://mirrors.kernel.org/archlinux/core/os/x86_64/core.files.tar.gz
        ./manage.py reporead --filesonly x86_64 core.files.tar.gz

Alter architecture and repo to get x86\_64 and packages from other repos if
needed.

8. Database Updates for Added/Removed packages

        sqlite3 archweb.db < packages/sql/update.sqlite3.sql

For PostgreSQL use packages/sql/update.postgresql_psycopg2.sql


# Testing SMTP server

To be able to create an account on your test environment an SMTP server is
required. A simple debugging SMTP server can be setup using Python.

        python -m smtpd -n -c DebuggingServer localhost:1025

In local\_settings.py add entries to set EMAIL\_HOST to 'localhost' and EMAIL\_PORT to
1025.

# Running tests and coverage

To the unittests execute the following commands:

        ./manage.py collectstatic --noinput
        ./manage.py test

Running coverage:

        pip install coverage
        coverage run --omit='env*' --source='.' manage.py test
        coverage report

# Django Debug toolbar

To use the Django Debug toolbar install django-debug-toolbar and in local_settings.py
set DEBUG_TOOLBAR to True.

# Management commands

Archweb provides multiple management commands for importing various sorts of data. An overview of commands:

* generate_keyring - Assemble a GPG keyring with all known developer keys.
* pgp_import - Import keys and signatures from a given GPG keyring.
* read_reproducible_status - Import rebuilderd status into Archweb.
* rematch_developers - Rematch flag requests and packages where user_id/packager_id is NULL to a Developer.
* reporead - Parses a repo.db.tar.gz, repo.files.tar.gz file and updates the Arch database with the relevant changes.
* reporead_inotify - Watches a templated patch for updates of *.files.tar.gz to update Arch databases with.
* donor_import - Import a single donator from a mail passed to stdin
* mirrorcheck - Poll every active mirror URLs to store the lastsnyc time and record network timing details.
* mirrorresolv - Poll every active mirror URLs and determine wheteher they have IP4 and/or IPv6 addresses.
* populate_signoffs - retrieves the latest commit message of a signoff-eligible package.
* update_planet - Import all feeds for users who have a valid website and website_rss in their user profile.

# Updating iPXE image

The netboot image can be updated by building the [AUR
package](https://aur.archlinux.org/packages/ipxe-netboot/) (note that it builds
from git master) and copying the resulting ipxe.pxe, ipxe.lkrn and ipxe.efi to
sitestatic/netboot. Then as Arch Linux Developer sign them with your PGP key
```gpg --output ipxe.efi.sig --detach-sig ipxe.efi```.

Testing a build iPXE image requires the 'qemu' package and running the
following command:

        qemu-system-x86_64 -kernel ipxe.lkrn -m 2G

# Production Installation

Arch Linux has an Ansible role for Archweb in their [infrastructure repo](https://git.archlinux.org/infrastructure.git/).

vim: set syntax=markdown et:
