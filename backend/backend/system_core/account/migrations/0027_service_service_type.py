# Generated by Django 4.1.6 on 2023-03-02 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0026_userdetail_manages'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='service_type',
            field=models.CharField(blank=True, choices=[('paid', 'Paid'), ('free', 'Free')], default='paid', max_length=50, null=True),
        ),
    ]
