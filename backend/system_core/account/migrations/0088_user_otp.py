# Generated by Django 4.1.6 on 2023-05-01 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0087_user_otp_expire'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp',
            field=models.CharField(blank=True, max_length=250, null=True, unique=True),
        ),
    ]