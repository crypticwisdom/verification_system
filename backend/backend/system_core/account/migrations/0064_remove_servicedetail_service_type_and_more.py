# Generated by Django 4.1.6 on 2023-03-18 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0063_transaction_document_transaction_document_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicedetail',
            name='service_type',
        ),
        migrations.AddField(
            model_name='service',
            name='service_type',
            field=models.CharField(blank=True, choices=[('paid', 'Paid'), ('free', 'Free')], default='paid', max_length=50, null=True),
        ),
    ]
