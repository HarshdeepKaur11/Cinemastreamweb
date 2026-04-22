

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0012_alter_recommendationfeedback_recommendation_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rating',
            name='is_recommended',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterModelTable(
            name='recommendationsessions',
            table='ml_models_recommendationsession',
        ),
    ]