

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('genre_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('genre_name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='MovieGenre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('genre', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.genre')),
            ],
        ),
        migrations.CreateModel(
            name='Movies',
            fields=[
                ('movie_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(max_length=2000)),
                ('director', models.CharField(max_length=100)),
                ('cast', models.TextField(max_length=100)),
                ('release_year', models.IntegerField()),
                ('language', models.CharField(max_length=100)),
                ('duration', models.FloatField()),
                ('runtime', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='MovieStats',
            fields=[
                ('stat_id', models.AutoField(primary_key=True, serialize=False)),
                ('total_views', models.PositiveIntegerField(default=0)),
                ('avg_rating', models.FloatField(default=0.0)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('movie', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stats', to='ml_models.movies')),
            ],
        ),
        migrations.DeleteModel(
            name='Todo',
        ),
        migrations.AddField(
            model_name='moviegenre',
            name='movie',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.movies'),
        ),
    ]