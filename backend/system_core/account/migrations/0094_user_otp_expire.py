# Generated by Django 4.1.6 on 2023-05-07 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0093_remove_user_otp_expire'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp_expire',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
