# Generated by Django 2.2.9 on 2020-01-08 00:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('terra', '0009_auto_20200107_2355'),
    ]

    operations = [
        migrations.RenameField(
            model_name='funding',
            old_name='approved_by',
            new_name='funded_by',
        ),
        migrations.RenameField(
            model_name='funding',
            old_name='approved_on',
            new_name='funded_on',
        ),
    ]
