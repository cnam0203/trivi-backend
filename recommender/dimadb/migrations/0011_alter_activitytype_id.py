# Generated by Django 3.2.5 on 2021-12-29 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dimadb', '0010_alter_products_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activitytype',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]