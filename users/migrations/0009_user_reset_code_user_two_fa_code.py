

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_genrepreference_delete_usergenrepreference'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='reset_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='two_fa_code',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]