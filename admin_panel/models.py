from django.conf import settings
from django.db import models


class TestRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_tests = models.IntegerField(default=0)
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    errors = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    current_test = models.CharField(max_length=500, blank=True, default='')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_runs',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TestRun #{self.pk} ({self.status})"


class TestResult(models.Model):
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('error', 'Error'),
        ('skipped', 'Skipped'),
    ]

    test_run = models.ForeignKey(
        TestRun,
        on_delete=models.CASCADE,
        related_name='results',
    )
    test_id = models.CharField(max_length=500)
    module = models.CharField(max_length=255)
    class_name = models.CharField(max_length=255)
    method = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    duration_ms = models.FloatField(default=0)
    output = models.TextField(blank=True, default='')
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test_id} ({self.status})"
