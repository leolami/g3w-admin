# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-27 15:59


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20160727_1449'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='header_logo_height',
        ),
    ]
