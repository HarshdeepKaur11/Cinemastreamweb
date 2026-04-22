

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0013_rating_is_recommended_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='moviestats',
            name='avg_completion',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='moviestats',
            name='total_watch_seconds',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='moviestats',
            name='wishlist_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='movies',
            name='backdrop_url_external',
            field=models.URLField(blank=True, max_length=2000, null=True),
        ),
        migrations.AlterField(
            model_name='movies',
            name='poster_url_external',
            field=models.URLField(blank=True, max_length=2000, null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='photo_url_external',
            field=models.URLField(blank=True, max_length=2000, null=True),
        ),
    ]