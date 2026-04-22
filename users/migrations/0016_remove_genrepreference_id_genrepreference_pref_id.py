

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_remove_genrepreference_id_genrepreference_pref_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='genrepreference',
            name='id',
        ),
        migrations.AddField(
            model_name='genrepreference',
            name='pref_id',
            field=models.BigAutoField(primary_key=True, serialize=False),
        ),
    ]