

from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0006_movies_backdrop'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='mlmodels',
            table='ml_models',
        ),
        migrations.AlterModelTable(
            name='moviestats',
            table='movie_stats',
        ),
        migrations.AlterModelTable(
            name='recommendationfeedback',
            table='recommendation_feedback',
        ),
        migrations.AlterModelTable(
            name='recommendations',
            table='recommendations',
        ),
        migrations.AlterModelTable(
            name='recommendationsessions',
            table='recommendation_sessions',
        ),
        migrations.AlterModelTable(
            name='userrating',
            table='user_ratings',
        ),
    ]