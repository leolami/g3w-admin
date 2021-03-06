# Generated by Django 2.2.16 on 2021-01-11 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qdjango', '0062_auto_20210104_1105'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='description_fi',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='project',
            name='description_se',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='project',
            name='title_ur_fi',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Public title'),
        ),
        migrations.AddField(
            model_name='project',
            name='title_ur_se',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Public title'),
        ),
    ]
