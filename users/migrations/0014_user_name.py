

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_user_is_verified_user_verification_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]