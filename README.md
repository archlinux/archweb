# Archweb README

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

4. Sync the database to create it.

        ./manage.py syncdb

5. Migrate changes.

        ./manage.py migrate

6. Load the fixtures to prepopulate some data. If you don't want some of the
   provided data, adjust the file glob accordingly.

        ./manage.py loaddata main/fixtures/*.json
        ./manage.py loaddata devel/fixtures/*.json
        ./manage.py loaddata mirrors/fixtures/*.json
        ./manage.py loaddata releng/fixtures/*.json

7. Use the following commands to start a service instance

        ./manage.py runserver

8. To optionally populate the database with real data:

        wget ftp://ftp.archlinux.org/core/os/i686/core.db.tar.gz
        ./manage.py reporead i686 core.db.tar.gz
        ./manage.py syncisos

Alter architecture and repo to get x86\_64 and packages from other repos if
needed.

# Production Installation

Ask someone who knows, or you are going to be in trouble.

vim: set syntax=markdown et:
