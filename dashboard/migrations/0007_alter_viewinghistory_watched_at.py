

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_searchhistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='viewinghistory',
            name='watched_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]