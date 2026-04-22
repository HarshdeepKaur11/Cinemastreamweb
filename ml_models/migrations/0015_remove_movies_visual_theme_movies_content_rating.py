

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0014_moviestats_avg_completion_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movies',
            name='visual_theme',
        ),
    ]