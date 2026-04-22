

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0017_alter_rating_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='movies',
            name='dominant_color',
            field=models.CharField(blank=True, help_text='Hex code or color name (e.g., #FFFFFF)', max_length=50, null=True),
        ),
    ]