# Generated by Django 4.1.6 on 2023-03-05 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0039_alter_transaction_document_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='payment_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]