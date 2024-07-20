# Generated by Django 4.1.6 on 2023-03-05 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0033_remove_service_discount_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicedetail',
            name='agency',
        ),
        migrations.RemoveField(
            model_name='service',
            name='agency',
        ),
        migrations.AddField(
            model_name='service',
            name='agency',
            field=models.ManyToManyField(help_text='If agencies can have more than 1 service.', to='account.userdetail'),
        ),
    ]
