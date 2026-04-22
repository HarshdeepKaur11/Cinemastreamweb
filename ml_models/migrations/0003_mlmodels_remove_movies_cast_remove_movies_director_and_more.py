

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0002_genre_moviegenre_movies_moviestats_delete_todo_and_more'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MLModels',
            fields=[
                ('model_id', models.AutoField(primary_key=True, serialize=False)),
                ('model_name', models.CharField(max_length=255)),
                ('model_type', models.CharField(max_length=100)),
                ('algorithm', models.CharField(max_length=100)),
                ('accuracy', models.FloatField()),
                ('weight', models.FloatField(default=0.5)),
                ('is_active', models.BooleanField(default=True)),
                ('trained_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='movies',
            name='cast',
        ),
        migrations.RemoveField(
            model_name='movies',
            name='director',
        ),
        migrations.RemoveField(
            model_name='movies',
            name='runtime',
        ),
        migrations.AlterField(
            model_name='movies',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='movies',
            name='duration',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='movies',
            name='title',
            field=models.CharField(max_length=255),
        ),
        migrations.CreateModel(
            name='Recommendations',
            fields=[
                ('recommendation_id', models.AutoField(primary_key=True, serialize=False)),
                ('score', models.FloatField()),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.movies')),
            ],
        ),
        migrations.CreateModel(
            name='RecommendationFeedback',
            fields=[
                ('feedback_id', models.AutoField(primary_key=True, serialize=False)),
                ('liked', models.BooleanField()),
                ('feedback_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
                ('recommendation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.recommendations')),
            ],
        ),
        migrations.CreateModel(
            name='RecommendationSessions',
            fields=[
                ('session_id', models.AutoField(primary_key=True, serialize=False)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('ml_model', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ml_models.mlmodels')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
        migrations.AddField(
            model_name='recommendations',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.recommendationsessions'),
        ),
        migrations.CreateModel(
            name='UserRating',
            fields=[
                ('rating_id', models.AutoField(primary_key=True, serialize=False)),
                ('rating', models.IntegerField()),
                ('rated_at', models.DateTimeField(auto_now_add=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.movies')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
    ]