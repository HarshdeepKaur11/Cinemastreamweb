

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0003_mlmodels_remove_movies_cast_remove_movies_director_and_more'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usergenrepreference',
            old_name='genre_id',
            new_name='genre',
        ),
        migrations.RenameField(
            model_name='usergenrepreference',
            old_name='user_id',
            new_name='user',
        ),
        migrations.AlterUniqueTogether(
            name='usergenrepreference',
            unique_together={('user', 'genre')},
        ),
        migrations.AlterModelTable(
            name='usergenrepreference',
            table='user_genre_preferences',
        ),
    ]