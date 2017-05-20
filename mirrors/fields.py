from IPy import IP

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models


class IPNetworkFormField(forms.Field):
    def to_python(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        try:
            value = IP(value)
        except ValueError as e:
            raise ValidationError(str(e))
        return value


class IPNetworkField(models.Field):
    description = "IPv4 or IPv6 address or subnet"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 44
        super(IPNetworkField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "IPAddressField"

    def to_python(self, value):
        if not value:
            return None
        return IP(value)

    def get_prep_value(self, value):
        value = self.to_python(value)
        if not value:
            return None
        return str(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': IPNetworkFormField}
        defaults.update(kwargs)
        return super(IPNetworkField, self).formfield(**defaults)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)
