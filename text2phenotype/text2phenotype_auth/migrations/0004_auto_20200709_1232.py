# Generated by Django 2.2.13 on 2020-07-09 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('text2phenotype_auth', '0003_text2phenotypeuser_is_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text2phenotypeuser',
            name='is_active',
        ),
        migrations.AddField(
            model_name='text2phenotypeuser',
            name='status',
            field=models.CharField(
                choices=[
                    ('STAGED', 'STAGED'),
                    ('PROVISIONED', 'PROVISIONED'),
                    ('ACTIVE', 'ACTIVE'),
                    ('RECOVERY', 'RECOVERY'),
                    ('LOCKED_OUT', 'LOCKED_OUT'),
                    ('PASSWORD_EXPIRED', 'PASSWORD_EXPIRED'),
                    ('SUSPENDED', 'SUSPENDED'),
                    ('DEPROVISIONED', 'DEPROVISIONED'),
                ],
                default='ACTIVE',
                max_length=16,
            ),
        ),
    ]
