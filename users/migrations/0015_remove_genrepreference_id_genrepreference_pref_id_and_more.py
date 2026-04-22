from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_user_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]