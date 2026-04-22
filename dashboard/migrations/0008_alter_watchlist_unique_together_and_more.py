
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_alter_viewinghistory_watched_at'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='watchlist',
            unique_together=set(),
        ),
        migrations.AlterModelTable(
            name='viewinghistory',
            table=None,
        ),
        migrations.AlterModelTable(
            name='watchlist',
            table=None,
        ),
    ]