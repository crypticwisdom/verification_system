# Generated by Django 4.1.6 on 2023-03-19 00:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0064_remove_servicedetail_service_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='logo',
            field=models.ImageField(default='default/agency.webp', null=True, upload_to='service/'),
        ),
        migrations.AlterField(
            model_name='servicedetail',
            name='logo',
            field=models.ImageField(default='default/agency.webp', null=True, upload_to='service/'),
        ),
    ]
