# Generated by Django 2.2.9 on 2020-03-02 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0058_auto_20200131_1008'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='description_en',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='group',
            name='description_it',
            field=models.TextField(blank=True, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='group',
            name='header_terms_of_use_text_en',
            field=models.TextField(blank=True, null=True, verbose_name='Terms of use text'),
        ),
        migrations.AddField(
            model_name='group',
            name='header_terms_of_use_text_it',
            field=models.TextField(blank=True, null=True, verbose_name='Terms of use text'),
        ),
        migrations.AddField(
            model_name='group',
            name='name_en',
            field=models.CharField(max_length=255, null=True, unique=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='group',
            name='name_it',
            field=models.CharField(max_length=255, null=True, unique=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='group',
            name='title_en',
            field=models.CharField(max_length=255, null=True, verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='group',
            name='title_it',
            field=models.CharField(max_length=255, null=True, verbose_name='Title'),
        ),
    ]
