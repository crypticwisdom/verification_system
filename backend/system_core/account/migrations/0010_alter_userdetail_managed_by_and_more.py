# Generated by Django 4.1.6 on 2023-02-22 08:49

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0009_remove_userdetail_managed_by_userdetail_managed_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetail',
            name='managed_by',
            field=models.ManyToManyField(blank=True, help_text='Expects a partner manager user profile to manage this Agency Profile', related_name='managers', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userdetail',
            name='user_type',
            field=models.CharField(blank=True, choices=[('platform', 'Platform'), ('agency', 'Agency'), ('individual', 'Individual'), ('corporate-business', 'Corporate-Business')], max_length=30, null=True),
        ),
        migrations.DeleteModel(
            name='UserType',
        ),
    ]
