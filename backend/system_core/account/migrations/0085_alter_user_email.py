# Generated by Django 4.1.6 on 2023-04-18 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0084_user_push_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=200, null=True, unique=True),
        ),
    ]
