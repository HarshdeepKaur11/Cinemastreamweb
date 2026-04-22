from django.db import models
from django.utils import timezone
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
from typing import TYPE_CHECKING

from django.db.models.signals import post_delete
from django.dispatch import receiver

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, null=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    admin_permissions = models.CharField(max_length=500, default='all')
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, null=True, blank=True)
    duration_preference = models.CharField(
        max_length=20,
        choices=[('Any', 'Any'), ('Short', 'Short (< 90m)'), ('Medium', 'Medium (90-150m)'), ('Long', 'Long (> 150m)')],
        default='Any'
    )
    language_preference = models.CharField(max_length=255, default='English', blank=True, null=True)
    two_fa_code = models.CharField(max_length=10, null=True, blank=True)
    reset_code = models.CharField(max_length=10, null=True, blank=True)
    password_last_updated = models.DateTimeField(null=True, blank=True)
    adult_content_filter = models.BooleanField(default=False)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.username if self.username else self.email

    def save(self, *args, **kwargs):

        is_new_upload = False
        if self.profile_pic:
            try:

                from django.core.files.uploadedfile import UploadedFile
                if isinstance(self.profile_pic.file, UploadedFile):
                    is_new_upload = True
            except (AttributeError, ValueError):
                pass

        if is_new_upload and self.profile_pic:
            try:
                img = Image.open(self.profile_pic)

                if img.mode != 'RGB':
                    img = img.convert('RGB')

                width, height = img.size
                if width != height:
                    min_dim = min(width, height)
                    left = (width - min_dim) / 2
                    top = (height - min_dim) / 2
                    right = (width + min_dim) / 2
                    bottom = (height + min_dim) / 2
                    img = img.crop((left, top, right, bottom))

                if img.height > 300 or img.width > 300:
                    img.thumbnail((300, 300), Image.Resampling.LANCZOS)

                tmp_buffer = BytesIO()
                img.save(tmp_buffer, format='JPEG', quality=80, optimize=True)

                curr_name = getattr(self.profile_pic, 'name', 'profile.jpg') or 'profile.jpg'
                file_name = os.path.basename(curr_name)
                self.profile_pic = ContentFile(tmp_buffer.getvalue(), name=file_name)
            except Exception as e:

                print(f"DEBUG: Profile pic optimization failed: {e}")

        super().save(*args, **kwargs)

@receiver(post_delete, sender=User)
def delete_user_profile_pic(sender, instance, **kwargs):

    if instance.profile_pic:
        if os.path.isfile(instance.profile_pic.path):
            os.remove(instance.profile_pic.path)

class GenrePreference(models.Model):
    if TYPE_CHECKING:
        user_id: int
        genre_id: int

    pref_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.ForeignKey('ml_models.Genre', on_delete=models.CASCADE)
    preference_score = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'genre')
        db_table = 'users_genrepreference'

    def __str__(self):
        return f"{self.user.username} likes {self.genre.genre_name}"