# Generated by Django 2.2.5 on 2020-01-22 22:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("terra", "0012_actualexpense_date_paid")]

    operations = [
        migrations.AddField(
            model_name="actualexpense",
            name="reimbursed",
            field=models.BooleanField(default=False),
        )
    ]
