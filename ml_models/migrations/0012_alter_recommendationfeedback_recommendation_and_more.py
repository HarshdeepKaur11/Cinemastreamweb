

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0011_remove_recommendations_movie_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recommendationfeedback',
            name='recommendation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.recommendation'),
        ),
        migrations.RemoveField(
            model_name='userrating',
            name='movie',
        ),
        migrations.RemoveField(
            model_name='userrating',
            name='user',
        ),
        migrations.AddField(
            model_name='movies',
            name='backdrop_url_external',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='movies',
            name='poster_url_external',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='photo_url_external',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='moviecast',
            unique_together={('movie', 'person')},
        ),
        migrations.DeleteModel(
            name='Recommendations',
        ),
        migrations.DeleteModel(
            name='UserRating',
        ),
    ]