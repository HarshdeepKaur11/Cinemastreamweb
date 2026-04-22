
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0018_movies_dominant_color'),
    ]

    operations = [
        migrations.AddField(
            model_name='moviestats',
            name='baseline_rating',
            field=models.FloatField(default=3.5, help_text="Initial 'Real Life' rating (IMDb-like)"),
        ),
        migrations.AddField(
            model_name='moviestats',
            name='baseline_weight',
            field=models.PositiveIntegerField(default=15, help_text='Weight of the baseline rating (virtual votes)'),
        ),
    ]