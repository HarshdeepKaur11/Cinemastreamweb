

import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0002_rename_genre_id_usergenrepreference_genre_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminActivityLog',
            fields=[
                ('log_id', models.AutoField(primary_key=True, serialize=False)),
                ('action', models.CharField(max_length=255)),
                ('target_entity', models.CharField(max_length=100)),
                ('action_time', models.DateTimeField(auto_now_add=True)),
                ('admin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.user')),
            ],
        ),
    ]