from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SYSTEM = 'SYSTEM', 'System'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    report = models.ForeignKey('reports.Report', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.report.id}"