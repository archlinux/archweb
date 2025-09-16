# Archweb README

[![Build Status](https://github.com/archlinux/archweb/actions/workflows/main.yml/badge.svg)](https://github.com/archlinux/archweb/actions/workflows/main.yml)

To get a pretty version of this document, run

    $ markdown README > README.html

# License

See LICENSE file.

# Authors

See AUTHORS file.

# Dependencies

- Python 3.13.0
- UV
- rsync (optional for mirrorcheck with rsync mirrors)

# Python dependencies

You can look at the packages `archweb` uses by looking at the `pyproject.toml` file;
it is best to use `uv` to handle these. If you insist on (Archlinux) packages, you
probably want the following:

- python-django
- python-psycopg2
- python-markdown
- python-memcached

# Testing Installation

1. Run `uv sync`.
2. Activate the virtualenv.
3. Copy `local_settings.py.example` to `local_settings.py` and modify.
   Make sure to uncomment the appropriate database section (either sqlite or
   PostgreSQL).
4. Migrate changes.

        uv run ./manage.py migrate
5. Load the fixtures to pre populate some data. If you don't want some of the
   provided data, adjust the file glob accordingly.

        uv run ./manage.py loaddata main/fixtures/*.json
        uv run ./manage.py loaddata devel/fixtures/*.json
        uv run ./manage.py loaddata mirrors/fixtures/*.json
        uv run ./manage.py loaddata releng/fixtures/*.json
6. Use the following commands to start a service instance

        uv ./manage.py runserver
7. To optionally populate the database with real data:

        wget http://mirrors.kernel.org/archlinux/core/os/x86_64/core.db.tar.gz
        uv run ./manage.py reporead x86_64 core.db.tar.gz
        # Package file listing
        wget http://mirrors.kernel.org/archlinux/core/os/x86_64/core.files.tar.gz
        uv run ./manage.py reporead --filesonly x86_64 core.files.tar.gz

Alter architecture and repo to get x86\_64 and packages from other repos if
needed.

8. Database Updates for Added/Removed packages

        sqlite3 archweb.db < packages/sql/update.sqlite3.sql

For PostgreSQL use packages/sql/update.postgresql_psycopg2.sql


# Testing SMTP server

To be able to create an account on your test environment an SMTP server is
required. A simple debugging SMTP server can be setup using Python and `aiosmtpd`.

Install `smtp` group

        uv sync --group smtp

Run the server

        uv run python -m aiosmtpd -n -l localhost:1025

In local\_settings.py add entries to set EMAIL\_HOST to 'localhost' and EMAIL\_PORT to
1025.

# Running tests and coverage

To run unittests execute the following commands:

        make collectstatic
        make test

Running coverage:

        make coverage
        make open-coverage

# Django Debug toolbar

To use the Django Debug toolbar install django-debug-toolbar and in local_settings.py
set DEBUG_TOOLBAR to True.

# Management commands

Archweb provides multiple management commands for importing various sorts of data. An overview of commands:

* generate_keyring - Assemble a GPG keyring with all known developer keys.
* pgp_import - Import keys and signatures from a given GPG keyring.
* read_rebuilderd_status - Import rebuilderd status into Archweb.
* rematch_developers - Rematch flag requests and packages where user_id/packager_id is NULL to a Developer.
* reporead - Parses a repo.db.tar.gz, repo.files.tar.gz file and updates the Arch database with the relevant changes.
* reporead_inotify - Watches a templated patch for updates of *.files.tar.gz to update Arch databases with.
* donor_import - Import a single donator from a mail passed to stdin
* mirrorcheck - Poll every active mirror URLs to store the lastsnyc time and record network timing details.
* mirrorresolv - Poll every active mirror URLs and determine whether they have IP4 and/or IPv6 addresses.
* populate_signoffs - retrieves the latest commit message of a signoff-eligible package.
* update_planet - Import all feeds for users who have a valid website and website_rss in their user profile.
* read_links - Reads a repo.links.db.tar.gz file and updates the Soname model.
* read_links_inotify - Watches a templated patch for updates of *.links.tar.gz to update Arch databases with.

# Updating iPXE images

The binaries required for iPXE based netboot are updated by copying them from
the [ipxe](https://archlinux.org/packages/extra/x86_64/ipxe/) package to
[the static content directory](/sitestatic/netboot/) (with the `run_ipxe`
script the binaries may be tested beforehand):

```
cp -v /usr/share/ipxe/x86_64/ipxe-arch.efi /usr/share/ipxe/ipxe-arch.{ipxe,lkrn} sitestatic/releng
```

Afterwards a detached PGP signature using a valid
[WKD](https://wiki.archlinux.org/title/GnuPG#Web_Key_Directory) enabled
[packager
key](https://gitlab.archlinux.org/archlinux/archlinux-keyring/-/wikis/home) is
created for each file:

```
for artifact in sitestatic/netboot/*.{efi,pxe,lkrn}; do
  gpg --sender "User Name <your@mail.address>" --detach-sign "$artifact"
done
```

# Production Installation

Arch Linux has an Ansible role for Archweb in their [infrastructure repo](https://gitlab.archlinux.org/archlinux/infrastructure).

vim: set syntax=markdown et:
