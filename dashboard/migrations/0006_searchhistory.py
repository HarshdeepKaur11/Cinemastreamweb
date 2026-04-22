

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_remove_wishlist_movie_remove_wishlist_user_and_more'),
        ('users', '0016_remove_genrepreference_id_genrepreference_pref_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('search_id', models.AutoField(primary_key=True, serialize=False)),
                ('query', models.CharField(max_length=255)),
                ('searched_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
            options={
                'db_table': 'dashboard_searchhistory',
            },
        ),
    ]