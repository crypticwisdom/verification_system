# Generated by Django 4.1.6 on 2023-03-09 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0048_alter_transaction_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='document',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='document_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
