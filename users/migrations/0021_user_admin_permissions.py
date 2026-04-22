

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_remove_user_is_super_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='admin_permissions',
            field=models.CharField(default='all', max_length=500),
        ),
    ]