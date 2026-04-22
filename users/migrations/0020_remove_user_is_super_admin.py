

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_user_is_super_admin'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_super_admin',
        ),
    ]