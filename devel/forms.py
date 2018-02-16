import random
from collections import OrderedDict
from string import ascii_letters, digits

from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template import loader

from .models import UserProfile


class ProfileForm(forms.Form):
    email = forms.EmailField(label='Private email (not shown publicly):',
            help_text="Used for out-of-date notifications, etc.")
    passwd1 = forms.CharField(label='New Password', required=False,
            widget=forms.PasswordInput)
    passwd2 = forms.CharField(label='Confirm Password', required=False,
            widget=forms.PasswordInput)

    def clean(self):
        if self.cleaned_data['passwd1'] != self.cleaned_data['passwd2']:
            raise forms.ValidationError('Passwords do not match.')
        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    def clean_pgp_key(self):
        data = self.cleaned_data['pgp_key']
        # strip 0x prefix if provided; store uppercase
        if data.startswith('0x'):
            data = data[2:]
        return data.upper()

    class Meta:
        model = UserProfile
        exclude = ('allowed_repos', 'user', 'latin_name')


class NewUserForm(forms.ModelForm):
    username = forms.CharField(max_length=30)
    private_email = forms.EmailField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    groups = forms.ModelMultipleChoiceField(required=False,
            queryset=Group.objects.all())

    class Meta:
        model = UserProfile
        exclude = ('picture', 'user')

    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)
        # Hack ourself so certain fields appear first
        old = self.fields
        self.fields = OrderedDict()
        keys = ('username', 'private_email', 'first_name', 'last_name',
                'alias', 'public_email')
        for key in keys:
            self.fields[key] = old[key]
        for key, _ in list(old.items()):
            if key not in keys:
                self.fields[key] = old[key]

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                    "A user with that username already exists.")
        return username

    def save(self, commit=True):
        profile = super(NewUserForm, self).save(False)
        pwletters = ascii_letters + digits
        password = ''.join([random.choice(pwletters) for _ in range(8)])
        user = User.objects.create_user(username=self.cleaned_data['username'],
                email=self.cleaned_data['private_email'], password=password)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        # sucks that the MRM.add() method can't take a list directly... we have
        # to resort to dirty * magic.
        user.groups.add(*self.cleaned_data['groups'])
        profile.user = user
        if commit:
            profile.save()
            self.save_m2m()

        template = loader.get_template('devel/new_account.txt')
        ctx = {
            'site': Site.objects.get_current(),
            'user': user,
            'password': password,
        }

        send_mail("Your new archweb account",
                template.render(ctx),
                'Arch Website Notification <nobody@archlinux.org>',
                [user.email],
                fail_silently=False)

# vim: set ts=4 sw=4 et:
