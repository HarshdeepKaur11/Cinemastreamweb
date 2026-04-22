

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_remove_user_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='adult_content_filter',
            field=models.BooleanField(default=False),
        ),
    ]
