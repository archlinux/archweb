# Archweb README

[![Build Status](https://travis-ci.org/archlinux/archweb.svg?branch=master)](https://travis-ci.org/archlinux/archweb)
[![Coverage Status](https://coveralls.io/repos/github/archlinux/archweb/badge.svg?branch=master)](https://coveralls.io/github/archlinux/archweb?branch=master)

To get a pretty version of this document, run

    $ markdown README > README.html

# License

See LICENSE file.

# Authors

See AUTHORS file.

# Dependencies

- python2
- python2-virtualenv

# Python dependencies

More detail in `requirements.txt` and `requirements_prod.txt`; it is best to
use virtualenv and pip to handle these. But if you insist on (Arch Linux)
packages, you will probably want the following:

- django
- python2-psycopg2
- python2-markdown
- python2-memcached

# Testing Installation

1. Run `virtualenv2`.

        cd /path/to/archweb && virtualenv2 ./env/

2. Activate the virtualenv.

        source ./env/bin/activate

2. Install dependencies through `pip`.

        pip install -r requirements.txt

3. Copy `local_settings.py.example` to `local_settings.py` and modify.
   Make sure to uncomment the appropriate database section (either sqlite or
   PostgreSQL).

4. Migrate changes.

        ./manage.py migrate

5. Load the fixtures to prepopulate some data. If you don't want some of the
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
        ./manage.py syncisos

Alter architecture and repo to get x86\_64 and packages from other repos if
needed.

# Testing SMTP server

To be able to create an account on your test environment an SMTP server is
required. A simple debugging SMTP server can be setup using Python.

        python2 -m smtpd -n -c DebuggingServer localhost:1025

In local_settings.py change the EMAIL_HOST to 'localhost' and the EMAIL_PORT to
1025.

# Running tests and coverage

To the unittests execute the following commands:

        ./manage.py collectstatic --noinput
        ./manage.py test

Running coverage:

        pip install coverage
        coverage run --omit='env*' --source='.' manage.py test
        coverage report


# Production Installation

Ask someone who knows, or you are going to be in trouble.

vim: set syntax=markdown et:
