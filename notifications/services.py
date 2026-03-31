from .models import Notification
from .tasks import send_email_notification_task

class NotificationService:
    @staticmethod
    def send_status_update(report):
        user = report.user
        base_message = f"Hello {user.username}, your report '{report.title}' status is now {report.get_status_display()}."
        
        # append staff remark if it exists
        if report.status_remark:
            full_message = f"{base_message}\n\nStaff Note: {report.status_remark}"
        else:
            full_message = base_message
        
        Notification.objects.create(
            user=user,
            report=report,
            subject=f"Update: {report.title}",
            message=full_message
        )

        send_email_notification_task.delay(
            user.email, 
            f"Update: {report.title}", 
            full_message
        )