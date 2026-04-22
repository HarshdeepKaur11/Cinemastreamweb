

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_bio_user_date_of_birth_alter_user_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='language_preference',
            field=models.CharField(blank=True, default='English', max_length=255, null=True),
        ),
    ]