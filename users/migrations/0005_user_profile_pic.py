

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_duration_preference'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_pic',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pics/'),
        ),
    ]