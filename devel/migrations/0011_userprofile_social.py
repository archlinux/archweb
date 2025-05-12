from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devel', '0010_merge_20230312_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='social',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
