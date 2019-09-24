# Generated by Django 2.2.5 on 2019-09-23 22:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('url', models.URLField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('city', models.CharField(max_length=32)),
                ('state', models.CharField(max_length=32)),
                ('country', models.CharField(default='USA', max_length=32)),
            ],
            options={
                'verbose_name_plural': 'Activities',
            },
        ),
        migrations.CreateModel(
            name='Approval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('approved_on', models.DateTimeField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=5, max_digits=10)),
                ('type', models.CharField(choices=[('S', 'Supervisor'), ('F', 'Funding'), ('I', 'International')], max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=32)),
                ('active', models.BooleanField(default=True)),
                ('uid', models.CharField(max_length=9, unique=True)),
                ('type', models.CharField(choices=[('EXEC', 'Executive'), ('HEAD', 'Unit Head'), ('LIBR', 'Librarian'), ('SENR', 'Sr. Exempt Staff'), ('OTHR', 'Other')], default='OTHR', max_length=4)),
                ('supervisor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='terra.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Fund',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.CharField(max_length=6)),
                ('cost_center', models.CharField(max_length=2)),
                ('fund', models.CharField(max_length=5)),
                ('manager', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='TravelRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('departure_date', models.DateField()),
                ('return_date', models.DateField()),
                ('days_ooo', models.IntegerField(verbose_name='Days Out of Office')),
                ('closed', models.BooleanField(default=False)),
                ('administrative', models.BooleanField(default=False)),
                ('justification', models.TextField(blank=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.Activity')),
                ('funds', models.ManyToManyField(through='terra.Approval', to='terra.Fund')),
                ('traveler', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.Employee')),
            ],
        ),
        migrations.CreateModel(
            name='Vacation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('treq', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='terra.TravelRequest')),
            ],
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('type', models.CharField(choices=[('1', 'Library'), ('2', 'Executive Division'), ('3', 'Managerial Unit')], max_length=1)),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='managed_units', to='terra.Employee')),
                ('parent_unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='subunits', to='terra.Unit')),
            ],
        ),
        migrations.CreateModel(
            name='EstimatedExpense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('LDG', 'Lodging'), ('AIR', 'Airfare'), ('TRN', 'Transit'), ('RNT', 'Car Rental'), ('DRV', 'Driving'), ('CON', 'Conference Registration'), ('PRE', 'Preconference Fees'), ('MEM', 'Membership Fees'), ('PRK', 'Parking'), ('EAT', 'Meals'), ('OTH', 'Other')], max_length=3)),
                ('rate', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('total', models.DecimalField(decimal_places=5, max_digits=10)),
                ('treq', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='terra.TravelRequest')),
            ],
        ),
        migrations.AddField(
            model_name='employee',
            name='unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.Unit'),
        ),
        migrations.AddField(
            model_name='employee',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='approval',
            name='approved_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.Employee'),
        ),
        migrations.AddField(
            model_name='approval',
            name='fund',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.Fund'),
        ),
        migrations.AddField(
            model_name='approval',
            name='treq',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.TravelRequest'),
        ),
        migrations.CreateModel(
            name='ActualExpense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('LDG', 'Lodging'), ('AIR', 'Airfare'), ('TRN', 'Transit'), ('RNT', 'Car Rental'), ('DRV', 'Driving'), ('CON', 'Conference Registration'), ('PRE', 'Preconference Fees'), ('MEM', 'Membership Fees'), ('PRK', 'Parking'), ('EAT', 'Meals'), ('OTH', 'Other')], max_length=3)),
                ('rate', models.DecimalField(blank=True, decimal_places=5, max_digits=10, null=True)),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('total', models.DecimalField(decimal_places=5, max_digits=10)),
                ('fund', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='terra.Fund')),
                ('treq', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='terra.TravelRequest')),
            ],
        ),
    ]
