import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_delete_adminactivitylog'),
        ('ml_models', '0010_remove_person_id_person_person_id_and_more'),
        ('users', '0007_user_language_preference'),
    ]

    operations = [
        migrations.CreateModel(
            name='ViewingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('watched_at', models.DateTimeField(auto_now_add=True)),
                ('time_spent_seconds', models.IntegerField(default=0)),
                ('click_count', models.IntegerField(default=1)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.movies')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'dashboard_viewinghistory',
            },
        ),
        migrations.CreateModel(
            name='Watchlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ml_models.movies')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'unique_together': {('user', 'movie')},
            },
        ),
    ]