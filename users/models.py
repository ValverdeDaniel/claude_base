import secrets
from django.conf import settings
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.username}"

    def is_valid(self):
        if self.used:
            return False
        expiry = self.created_at + timezone.timedelta(hours=24)
        return timezone.now() < expiry

    def mark_as_used(self):
        self.used = True
        self.save(update_fields=['used'])

    @classmethod
    def generate_token(cls):
        return secrets.token_urlsafe(48)
