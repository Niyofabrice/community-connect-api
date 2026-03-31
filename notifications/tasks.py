from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger('apps.notifications')

@shared_task(bind=True, max_retries=3)
def send_email_notification_task(self, recipient_email, subject, message):
    logger.info(f"Attempting to send email to {recipient_email}")
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        logger.info(f"Email successfully sent to {recipient_email}")
    except Exception as exc:
        logger.error(f"Failed to send email to {recipient_email}. Reason: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)