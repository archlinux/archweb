# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0002_auto_20160731_0556'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flagrequest',
            name='user_email',
            field=models.EmailField(max_length=254, verbose_name=b'email address'),
        ),
    ]
