# Generated by Django 4.1.6 on 2023-03-16 19:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0058_alter_transaction_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='service',
            old_name='is_active',
            new_name='activate',
        ),
        migrations.RenameField(
            model_name='servicedetail',
            old_name='is_active',
            new_name='is_available',
        ),
    ]
