#!/bin/bash
cd /home/sites/archlinux/archlinux
export PYTHONPATH=/usr/local/django:/home/sites/archlinux:${PYTHONPATH}
export DJANGO_SETTINGS_MODULE=archlinux.settings
python manage.py $*

