

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_genrepreference_preference_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=150, null=True, unique=True),
        ),
    ]