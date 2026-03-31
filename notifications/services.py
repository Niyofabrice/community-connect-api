from .models import Notification
from .tasks import send_email_notification_task
import logging

logger = logging.getLogger('apps.notifications')

class NotificationService:
    @staticmethod
    def send_status_update(report):
        user = report.user
        logger.info(f"Initiating status update notification for Report ID: {report.id}, User: {user.username}")

        base_message = f"Hello {user.username}, your report '{report.title}' status is now {report.get_status_display()}."
        
        # append staff remark if it exists
        if report.status_remark:
            logger.debug(f"Adding staff remark to notification for Report {report.id}")
            full_message = f"{base_message}\n\nStaff Note: {report.status_remark}"
        else:
            full_message = base_message
        
        try:
            notification = Notification.objects.create(
                user=user,
                report=report,
                subject=f"Update: {report.title}",
                message=full_message
            )
            logger.info(f"Notification record created in DB (ID: {notification.id})")
        except Exception as e:
            logger.error(f"Failed to create Notification record for Report {report.id}: {str(e)}", exc_info=True)

        try:
            logger.debug(f"Queueing email task for {user.email}")
            send_email_notification_task.delay(
                user.email,
                f"Update: {report.title}",
                full_message
            )
            logger.info(f"Email task successfully queued for User: {user.username}")
        except Exception as e:
            logger.error(f"Failed to queue email task for Report {report.id}: {str(e)}", exc_info=True)