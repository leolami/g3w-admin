# Generated by Django 2.2.13 on 2020-08-10 06:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qdjango', '0051_project_layouts'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='download_csv',
            field=models.BooleanField(blank=True, default=False, verbose_name='Download data in csv format'),
        ),
    ]