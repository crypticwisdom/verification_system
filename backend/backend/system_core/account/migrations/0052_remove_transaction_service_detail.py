# Generated by Django 4.1.6 on 2023-03-10 03:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0051_alter_transaction_service_detail'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='service_detail',
        ),
    ]