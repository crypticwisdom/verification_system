# Generated by Django 4.1.6 on 2023-03-05 19:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0044_transaction_agency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetail',
            name='state',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='account.state'),
        ),
    ]