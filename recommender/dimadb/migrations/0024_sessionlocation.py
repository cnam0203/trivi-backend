# Generated by Django 3.2.5 on 2022-01-03 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dimadb', '0023_rename_sessiondata_session'),
    ]

    operations = [
        migrations.CreateModel(
            name='SessionLocation',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('session_id', models.CharField(blank=True, max_length=50, null=True)),
                ('location_id', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
    ]
