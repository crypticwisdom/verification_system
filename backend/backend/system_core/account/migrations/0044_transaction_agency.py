# Generated by Django 4.1.6 on 2023-03-05 19:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0043_alter_transaction_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='agency',
            field=models.ForeignKey(blank=True, help_text='Agenc service used.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='agency', to=settings.AUTH_USER_MODEL),
        ),
    ]
