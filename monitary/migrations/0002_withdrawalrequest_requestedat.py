# Generated by Django 5.1.4 on 2025-03-14 14:33

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitary', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='withdrawalrequest',
            name='requestedAt',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
