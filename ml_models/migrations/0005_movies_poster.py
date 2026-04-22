

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0004_alter_genre_genre_id_alter_genre_genre_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='movies',
            name='poster',
            field=models.ImageField(blank=True, null=True, upload_to='posters/'),
        ),
    ]