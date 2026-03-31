from django.test import TestCase
from django.core import mail
from users.models import User
from reports.models import Report, Category
from notifications.models import Notification

class NotificationSignalTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", 
            email="nf.niyonkuru.fabrice@gmail.com", 
            password="password123",
            role=User.Role.CITIZEN
        )
        self.category = Category.objects.create(name="Infrastructure")
        
        self.report = Report.objects.create(
            title="Broken Pipe",
            description="Water is leaking",
            user=self.user,
            category=self.category,
            status=Report.Status.PENDING
        )

    def test_notification_sent_on_status_change(self):
        """Test that changing status triggers an email and logs a Notification."""
        
        # Change status to RESOLVED
        self.report.status = Report.Status.RESOLVED
        self.report.save()

        # Check 1: Was a Notification object created in the DB?
        notification_exists = Notification.objects.filter(
            user=self.user, 
            report=self.report
        ).exists()
        self.assertTrue(notification_exists, "Notification record was not created in the database.")

        self.assertEqual(len(mail.outbox), 1, "Exactly one email should have been sent.")
        self.assertIn("Resolved", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_no_notification_on_other_updates(self):
        """Test that changing the description does NOT trigger a notification."""
        
        # Clear outbox from setup/creation
        mail.outbox = []
        
        self.report.description = "Updated description"
        self.report.save()

        self.assertEqual(len(mail.outbox), 0, "No email should be sent for description updates.")