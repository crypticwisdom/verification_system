# Generated by Django 4.1.6 on 2023-05-01 20:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0086_servicedetail_added_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp_expire',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
