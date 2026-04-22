

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0020_movies_content_descriptor_movies_publisher'),
    ]

    operations = [
        migrations.AddField(
            model_name='mlmodels',
            name='version',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='mlmodels',
            name='trained_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
