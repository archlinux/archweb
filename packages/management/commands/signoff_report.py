# -*- coding: utf-8 -*-
"""
signoff_report command

Send an email summarizing the state of outstanding signoffs for the given
repository.

Usage: ./manage.py signoff_report <email> <repository>
"""

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db.models import Count
from django.template import loader, Context
from django.utils.timezone import now

from collections import namedtuple
from datetime import timedelta
import logging
from operator import attrgetter
import sys

from main.models import Repo
from packages.models import Signoff
from packages.utils import get_signoff_groups

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s -> %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stderr)
logger = logging.getLogger()

class Command(BaseCommand):
    args = "<email> <repository>"
    help = "Send a signoff report for the given repository."

    def handle(self, *args, **options):
        v = int(options.get('verbosity', None))
        if v == 0:
            logger.level = logging.ERROR
        elif v == 1:
            logger.level = logging.INFO
        elif v == 2:
            logger.level = logging.DEBUG

        if len(args) != 2:
            raise CommandError("email and repository must be provided")

        return generate_report(args[0], args[1])

def generate_report(email, repo_name):
    repo = Repo.objects.get(name__iexact=repo_name)
    # Collect all existing signoffs for these packages
    signoff_groups = sorted(get_signoff_groups([repo]),
            key=attrgetter('target_repo', 'arch', 'pkgbase'))
    disabled = []
    bad = []
    complete = []
    incomplete = []
    new = []
    old = []

    new_hours = 24
    old_days = 14
    current_time = now()
    new_cutoff = current_time - timedelta(hours=new_hours)
    old_cutoff = current_time - timedelta(days=old_days)

    if len(signoff_groups) == 0:
        # no need to send an email at all
        return

    for group in signoff_groups:
        spec = group.specification
        if spec.known_bad:
            bad.append(group)
        elif not spec.enabled:
            disabled.append(group)
        elif group.approved():
            complete.append(group)
        else:
            incomplete.append(group)

        if group.package.last_update > new_cutoff:
            new.append(group)
        if group.package.last_update < old_cutoff:
            old.append(group)

    old.sort(key=attrgetter('last_update'))

    proto = 'https'
    domain = Site.objects.get_current().domain
    signoffs_url = '%s://%s%s' % (proto, domain, reverse('package-signoffs'))

    # and the fun bit
    Leader = namedtuple('Leader', ['user', 'count'])
    leaders = Signoff.objects.filter(created__gt=new_cutoff,
            revoked__isnull=True).values_list('user').annotate(
                    signoff_count=Count('pk')).order_by('-signoff_count')[:5]
    users = User.objects.in_bulk([l[0] for l in leaders])
    leaders = (Leader(users[l[0]], l[1]) for l in leaders)

    subject = 'Signoff report for [%s]' % repo.name.lower()
    t = loader.get_template('packages/signoff_report.txt')
    c = Context({
        'repo': repo,
        'signoffs_url': signoffs_url,
        'disabled': disabled,
        'bad': bad,
        'all': signoff_groups,
        'incomplete': incomplete,
        'complete': complete,
        'new': new,
        'new_hours': new_hours,
        'old': old,
        'old_days': old_days,
        'leaders': leaders,
    })
    from_addr = 'Arch Website Notification <nobody@archlinux.org>'
    send_mail(subject, t.render(c), from_addr, [email])

# vim: set ts=4 sw=4 et:
