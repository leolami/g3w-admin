# Generated by Django 2.2.16 on 2021-03-08 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qdjango', '0067_auto_20210308_0947'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='autozoom_query',
            field=models.BooleanField(default=False, help_text='Automatic zoom on query result features for only one layer', verbose_name='Automatic zoom to query result features'),
        ),
    ]
