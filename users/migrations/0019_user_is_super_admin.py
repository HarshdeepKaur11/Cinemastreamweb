

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_user_otp_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_super_admin',
            field=models.BooleanField(default=False),
        ),
    ]