# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-17 07:51
from __future__ import unicode_literals
from django.db import migrations, models
import django.db.models.deletion
from text2phenotype.text2phenotype_auth.models.text2phenotype_base import generate_uuid
from text2phenotype.text2phenotype_auth.models.text2phenotype_user import make_unusable_password


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('sessions', '0001_initial'),
    ]



    operations = [
        migrations.CreateModel(
            name='Destination',
            fields=[
                ('uuid', models.CharField(db_index=True, default=generate_uuid, max_length=32)),
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('internal', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EmailAddress',
            fields=[
                ('uuid', models.CharField(db_index=True, default=generate_uuid, max_length=32)),
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('primary', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Text2phenotypeUser',
            fields=[
                ('uuid', models.CharField(db_index=True, default=generate_uuid, max_length=32)),
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('middle_initial', models.CharField(blank=True, max_length=1, null=True)),
                ('display_name', models.CharField(blank=True, max_length=255, null=True)),
                ('organization', models.CharField(blank=True, max_length=255, null=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sub', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('login_attempt_count', models.IntegerField(default=0)),
                ('access_token', models.TextField(blank=True, null=True)),
                ('access_expiry', models.DateTimeField(blank=True, null=True)),
                ('password', models.CharField(default=make_unusable_password, max_length=128)),
                ('text2phenotype_provisioned', models.BooleanField(default=True)),
                ('destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='text2phenotype_auth.Destination')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OAuth2Flow',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('session', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='sessions.Session')),
                ('state', models.TextField()),
                ('nonce', models.TextField()),
                ('redirect_url', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sessions.Session')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='text2phenotype_auth.Text2phenotypeUser')),
            ],
        ),
        migrations.AddField(
            model_name='emailaddress',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emails', to='text2phenotype_auth.Text2phenotypeUser'),
        ),
    ]

