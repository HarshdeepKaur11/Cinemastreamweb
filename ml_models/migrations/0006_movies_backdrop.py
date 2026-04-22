

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0005_movies_poster'),
    ]

    operations = [
        migrations.AddField(
            model_name='movies',
            name='backdrop',
            field=models.ImageField(blank=True, null=True, upload_to='backdrops/'),
        ),
    ]