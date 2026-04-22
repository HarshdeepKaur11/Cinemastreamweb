

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_user_username'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='name',
        ),
    ]