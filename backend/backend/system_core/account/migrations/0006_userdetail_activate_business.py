# Generated by Django 4.1.6 on 2023-02-21 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0005_user_super_admin_has_reset_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdetail',
            name='activate_business',
            field=models.BooleanField(default=False),
        ),
    ]
