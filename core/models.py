from typing import TYPE_CHECKING, Any, Optional
from django.db import models

class ContactMessage(models.Model):
    if TYPE_CHECKING:
        id: int
        status_info: Optional[dict[str, Any]]
        current_status: Optional[dict[str, Any]]

    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    status_info = None
    current_status = None

    def __str__(self):
        return f"{self.subject} - {self.email}"