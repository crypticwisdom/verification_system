# Generated by Django 4.1.6 on 2023-03-21 23:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0069_remove_service_service_code_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='service_type',
        ),
    ]