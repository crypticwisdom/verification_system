# Generated by Django 4.1.6 on 2023-05-26 19:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0102_transaction_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='transaction',
            old_name='name',
            new_name='full_name',
        ),
    ]
