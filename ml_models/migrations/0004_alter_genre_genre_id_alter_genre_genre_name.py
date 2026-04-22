

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0003_mlmodels_remove_movies_cast_remove_movies_director_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='genre',
            name='genre_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='genre',
            name='genre_name',
            field=models.CharField(max_length=100),
        ),
    ]