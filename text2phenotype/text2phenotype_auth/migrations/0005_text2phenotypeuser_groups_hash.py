# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-09-11 08:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('text2phenotype_auth', '0004_auto_20200709_1232'),
    ]

    operations = [
        migrations.AddField(
            model_name='text2phenotypeuser',
            name='groups_hash',
            field=models.CharField(blank=True, max_length=65, null=True),
        ),
    ]
