

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0008_movies_visual_theme'),
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('role', models.CharField(choices=[('actor', 'Actor'), ('director', 'Director')], max_length=20)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='persons/')),
            ],
        ),
        migrations.AddField(
            model_name='movies',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='movies',
            name='trailer_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userrating',
            name='review',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userrating',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='genre',
            name='genre_name',
            field=models.CharField(db_column='name', max_length=100),
        ),
        migrations.AlterField(
            model_name='movies',
            name='duration',
            field=models.IntegerField(blank=True, db_column='duration_minutes', null=True),
        ),
        migrations.AlterField(
            model_name='userrating',
            name='rated_at',
            field=models.DateTimeField(auto_now_add=True, db_column='created_at', null=True),
        ),
        migrations.AlterField(
            model_name='userrating',
            name='rating',
            field=models.IntegerField(db_column='score'),
        ),
        migrations.AlterModelTable(
            name='genre',
            table='ml_models_genre',
        ),
        migrations.AlterModelTable(
            name='moviegenre',
            table='ml_models_moviegenre',
        ),
        migrations.AlterModelTable(
            name='movies',
            table='ml_models_movies',
        ),
        migrations.AlterModelTable(
            name='userrating',
            table='ml_models_rating',
        ),
        migrations.CreateModel(
            name='MovieCast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('character_name', models.CharField(blank=True, max_length=200)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.movies')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.person')),
            ],
        ),
    ]