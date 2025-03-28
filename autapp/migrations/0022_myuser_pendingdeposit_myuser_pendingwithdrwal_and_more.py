# Generated by Django 5.1.4 on 2025-03-11 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autapp', '0021_alter_ingame_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='pendingDeposit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='myuser',
            name='pendingWithdrwal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='myuser',
            name='withdrawalToken',
            field=models.IntegerField(null=True),
        ),
    ]
