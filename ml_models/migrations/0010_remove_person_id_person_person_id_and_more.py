

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0009_person_movies_created_at_movies_trailer_url_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='person',
            name='id',
        ),
        migrations.AddField(
            model_name='person',
            name='person_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterModelTable(
            name='moviecast',
            table='ml_models_moviecast',
        ),
        migrations.AlterModelTable(
            name='person',
            table='ml_models_person',
        ),
    ]