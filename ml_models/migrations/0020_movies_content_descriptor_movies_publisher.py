
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0019_moviestats_baseline_rating_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='movies',
            name='content_descriptor',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='movies',
            name='publisher',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]