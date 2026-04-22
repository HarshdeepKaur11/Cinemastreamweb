

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_profile_pic'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterModelTable(
            name='usergenrepreference',
            table='users_genrepreference',
        ),
    ]