from django.db import models
from users.models import User

class AdminActivityLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    target_entity = models.CharField(max_length=100)
    action_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        admin_name = self.admin.name if self.admin.name else self.admin.username
        return f"{admin_name} - {self.action}"