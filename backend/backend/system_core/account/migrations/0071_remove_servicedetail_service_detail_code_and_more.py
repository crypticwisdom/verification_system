# Generated by Django 4.1.6 on 2023-03-22 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0070_remove_service_service_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicedetail',
            name='service_detail_code',
        ),
        migrations.AddField(
            model_name='service',
            name='service_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]