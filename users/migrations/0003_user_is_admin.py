

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_rename_genre_id_usergenrepreference_genre_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
    ]