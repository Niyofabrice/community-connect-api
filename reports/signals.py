from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Report
from notifications.services import NotificationService

@receiver(pre_save, sender=Report)
def track_status_change(sender, instance, **kwargs):
    if instance.pk:
        previous_version = Report.objects.only('status').get(pk=instance.pk)
        instance._old_status = previous_version.status
    else:
        instance._old_status = None

@receiver(post_save, sender=Report)
def notify_status_change(sender, instance, created, **kwargs):
    if not created:
        if instance.status != getattr(instance, '_old_status', None) or instance.status_remark:
            NotificationService.send_status_update(instance)
            Report.objects.filter(pk=instance.pk).update(status_remark="")