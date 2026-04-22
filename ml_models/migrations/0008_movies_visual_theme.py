

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('ml_models', '0007_alter_mlmodels_table_alter_moviestats_table_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='movies',
            name='visual_theme',
            field=models.CharField(blank=True, help_text="e.g., 'Dark', 'Vibrant', 'Minimalist'", max_length=100, null=True),
        ),
    ]