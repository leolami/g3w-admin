# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-12-19 13:53


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_auto_20161216_1657'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalsuitedata',
            name='about_tel',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='About phone'),
        ),
    ]
