from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger('apps.notifications')

@shared_task(bind=True, max_retries=3)
def send_email_notification_task(self, recipient_email, subject, message):
    attempt = self.request.retries + 1
    logger.info(f"Email Task: Attempt {attempt} for {recipient_email}")
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        logger.info(f"Email Task: Success for {recipient_email} on attempt {attempt}")
    except Exception as exc:
        logger.error(f"Email Task: Failed attempt {attempt} for {recipient_email}. Error: {exc}")
        raise self.retry(exc=exc, countdown=60)