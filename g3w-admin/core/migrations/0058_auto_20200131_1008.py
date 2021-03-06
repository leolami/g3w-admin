# Generated by Django 2.2.9 on 2020-01-31 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_auto_20200103_0816'),
    ]

    operations = [
        migrations.AddField(
            model_name='generalsuitedata',
            name='about_description_en',
            field=models.TextField(blank=True, null=True, verbose_name='About description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='about_description_it',
            field=models.TextField(blank=True, null=True, verbose_name='About description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='about_name_en',
            field=models.CharField(max_length=255, null=True, verbose_name='About name'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='about_name_it',
            field=models.CharField(max_length=255, null=True, verbose_name='About name'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='about_title_en',
            field=models.CharField(max_length=255, null=True, verbose_name='About title'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='about_title_it',
            field=models.CharField(max_length=255, null=True, verbose_name='About title'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='credits_en',
            field=models.TextField(blank=True, null=True, verbose_name='Credits'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='credits_it',
            field=models.TextField(blank=True, null=True, verbose_name='Credits'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='groups_map_description_en',
            field=models.TextField(blank=True, null=True, verbose_name='Groups map description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='groups_map_description_it',
            field=models.TextField(blank=True, null=True, verbose_name='Groups map description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='groups_title_en',
            field=models.CharField(max_length=255, null=True, verbose_name='Groups title'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='groups_title_it',
            field=models.CharField(max_length=255, null=True, verbose_name='Groups title'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='home_description_en',
            field=models.TextField(blank=True, null=True, verbose_name='Home description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='home_description_it',
            field=models.TextField(blank=True, null=True, verbose_name='Home description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='login_description_en',
            field=models.TextField(blank=True, null=True, verbose_name='Login description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='login_description_it',
            field=models.TextField(blank=True, null=True, verbose_name='Login description'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='main_map_title_en',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Main map title'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='main_map_title_it',
            field=models.CharField(blank=True, max_length=400, null=True, verbose_name='Main map title'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='sub_title_en',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Subtitle'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='sub_title_it',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Subtitle'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='title_en',
            field=models.CharField(max_length=255, null=True, verbose_name='Title'),
        ),
        migrations.AddField(
            model_name='generalsuitedata',
            name='title_it',
            field=models.CharField(max_length=255, null=True, verbose_name='Title'),
        ),
    ]
