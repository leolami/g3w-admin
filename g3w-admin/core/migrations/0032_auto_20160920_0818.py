# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-20 08:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_remove_mapcontrol_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mapcontrol',
            options={'ordering': ('order',), 'verbose_name': 'Map control', 'verbose_name_plural': 'Map controls'},
        ),
        migrations.AddField(
            model_name='mapcontrol',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=1, editable=False),
            preserve_default=False,
        ),
    ]
