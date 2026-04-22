

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_user_adult_content_filter'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='otp_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]