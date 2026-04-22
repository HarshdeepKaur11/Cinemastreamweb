

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0011_remove_recommendations_movie_and_more'),
        ('users', '0007_user_language_preference'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenrePreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('genre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.genre')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'users_genrepreference',
                'unique_together': {('user', 'genre')},
            },
        ),
        migrations.DeleteModel(
            name='UserGenrePreference',
        ),
    ]