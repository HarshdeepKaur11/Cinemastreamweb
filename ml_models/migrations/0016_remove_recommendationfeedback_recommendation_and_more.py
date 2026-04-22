

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0015_remove_movies_visual_theme_movies_content_rating'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recommendationfeedback',
            name='recommendation',
        ),
        migrations.RemoveField(
            model_name='recommendationfeedback',
            name='user',
        ),
        migrations.RemoveField(
            model_name='recommendationsessions',
            name='ml_model',
        ),
        migrations.RemoveField(
            model_name='recommendationsessions',
            name='user',
        ),
        migrations.AddField(
            model_name='movies',
            name='content_rating',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='moviecast',
            name='movie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movie_casts', to='ml_models.movies'),
        ),
        migrations.AlterField(
            model_name='moviecast',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movie_casts', to='ml_models.person'),
        ),
        migrations.AlterField(
            model_name='moviegenre',
            name='genre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movie_genres', to='ml_models.genre'),
        ),
        migrations.AlterField(
            model_name='moviegenre',
            name='movie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movie_genres', to='ml_models.movies'),
        ),
        migrations.DeleteModel(
            name='Recommendation',
        ),
        migrations.DeleteModel(
            name='RecommendationFeedback',
        ),
        migrations.DeleteModel(
            name='RecommendationSessions',
        ),
    ]