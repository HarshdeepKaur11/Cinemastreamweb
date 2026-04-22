

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_user_is_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='duration_preference',
            field=models.CharField(choices=[('Any', 'Any'), ('Short', 'Short (< 90m)'), ('Medium', 'Medium (90-150m)'), ('Long', 'Long (> 150m)')], default='Any', max_length=20),
        ),
    ]