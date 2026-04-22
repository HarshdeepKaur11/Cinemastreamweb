

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_clean_up_migrations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wishlist',
            name='movie',
        ),
        migrations.RemoveField(
            model_name='wishlist',
            name='user',
        ),
        migrations.RemoveField(
            model_name='viewinghistory',
            name='id',
        ),
        migrations.RemoveField(
            model_name='watchlist',
            name='id',
        ),
        migrations.AddField(
            model_name='viewinghistory',
            name='history_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AddField(
            model_name='viewinghistory',
            name='progress',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='viewinghistory',
            name='trailer_watch_seconds',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='watchlist',
            name='wishlist_id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterModelTable(
            name='watchlist',
            table='dashboard_watchlist',
        ),
        migrations.DeleteModel(
            name='WatchHistory',
        ),
        migrations.DeleteModel(
            name='Wishlist',
        ),
    ]