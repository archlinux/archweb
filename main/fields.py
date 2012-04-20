from django.db import models


class PositiveBigIntegerField(models.BigIntegerField):
    _south_introspects = True

    def get_internal_type(self):
        return "BigIntegerField"

    def formfield(self, **kwargs):
        defaults = { 'min_value': 0 }
        defaults.update(kwargs)
        return super(PositiveBigIntegerField, self).formfield(**defaults)

# vim: set ts=4 sw=4 et:
