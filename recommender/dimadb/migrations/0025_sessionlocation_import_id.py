# Generated by Django 3.2.5 on 2022-01-03 20:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dimadb', '0024_sessionlocation'),
    ]

    operations = [
        migrations.AddField(
            model_name='sessionlocation',
            name='import_id',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
