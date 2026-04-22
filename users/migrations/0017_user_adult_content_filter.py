

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_remove_genrepreference_id_genrepreference_pref_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='adult_content_filter',
            field=models.BooleanField(default=True),
        ),
    ]