# Generated by Django 4.1.6 on 2023-05-18 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0099_servicedetail_parent_agency'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicedetail',
            name='domain_url',
            field=models.CharField(blank=True, default='', help_text='This field is used to hold the url of an agency, needed in V2.', max_length=200, null=True),
        ),
    ]
