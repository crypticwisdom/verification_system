# Generated by Django 4.1.6 on 2023-02-27 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0022_alter_userrole_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userrole',
            name='user_role',
            field=models.CharField(choices=[('super-admin', 'Super-Admin'), ('partner-manager', 'Partner-Manager'), ('individual', 'Individual'), ('developer', 'Developer'), ('agency', 'Agency'), ('sub-agency', 'Sub-Agency'), ('corporate-business', 'Corporate-Business'), ('sub-corporate-business', 'Sub-Corporate-Business')], default='super-admin', max_length=100),
        ),
    ]
