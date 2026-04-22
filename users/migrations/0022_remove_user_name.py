
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0021_user_admin_permissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='name',
        ),
    ]