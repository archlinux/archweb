# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signoffspecification',
            name='known_bad',
            field=models.BooleanField(default=False, help_text=b'Is this package known to be broken in some way?'),
            preserve_default=True,
        ),
    ]
