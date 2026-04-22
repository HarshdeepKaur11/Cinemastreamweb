

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_user_reset_code_user_two_fa_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='genrepreference',
            name='preference_score',
            field=models.FloatField(default=1.0),
        ),
    ]