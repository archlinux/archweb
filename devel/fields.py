from django.db import models
from django.core.validators import RegexValidator


class PGPKeyField(models.CharField):
    _south_introspects = True

    def __init__(self, *args, **kwargs):
        super(PGPKeyField, self).__init__(*args, **kwargs)
        self.validators.append(RegexValidator(r'^[0-9A-F]{40}$',
            "Ensure this value consists of 40 hex characters.", 'hex_char'))

    def to_python(self, value):
        if value == '' or value is None:
            return None
        value = super(PGPKeyField, self).to_python(value)
        # remove all spaces
        value = value.replace(' ', '')
        # prune prefixes, either 0x or 2048R/ type
        if value.startswith('0x'):
            value = value[2:]
        value = value.split('/')[-1]
        # make all (hex letters) uppercase
        return value.upper()

    def formfield(self, **kwargs):
        # override so we don't set max_length form field attribute
        return models.Field.formfield(self, **kwargs)

# vim: set ts=4 sw=4 et:
