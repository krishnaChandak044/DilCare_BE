"""
Notification Service — Handles push notifications via Expo API.
Used by various endpoints to send notifications to users.
"""
import requests
import uuid
import logging
from typing import Optional, Dict, List
from django.contrib.auth.models import User
from accounts.models import UserDevice, Notification, NotificationPreference


logger = logging.getLogger(__name__)

# Expo Push Notifications API endpoint
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class NotificationService:
    """Service for sending push notifications via Expo."""

    @staticmethod
    def send_to_user(
        user: User,
        title: str,
        body: str,
        notification_type: str = "other",
        action: str = "",
        data: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Send a push notification to a specific user.
        
        Args:
            user: User object to send notification to
            title: Notification title
            body: Notification body/message
            notification_type: Type of notification (sos_alert, medication_reminder, etc.)
            action: Action type for the app to handle
            data: Additional data to send with the notification
            
        Returns:
            Notification ID if successful, None if failed
        """
        # Check notification preferences
        try:
            prefs = user.notification_preferences
            if not prefs.should_send_notification(notification_type):
                logger.info(f"Notification skipped for {user.email} - preference disabled")
                return None
        except NotificationPreference.DoesNotExist:
            pass  # Send if no preferences set

        # Get user's active devices
        devices = UserDevice.objects.filter(user=user, is_active=True)
        
        if not devices.exists():
            logger.warning(f"No active devices for user {user.email}")
            return None

        notification_id = f"notif-{uuid.uuid4()}"
        data = data or {}

        # Track successful sends
        successful_sends = 0

        # Send to each device
        for device in devices:
            try:
                payload = {
                    "to": device.device_token,
                    "title": title,
                    "body": body,
                    "data": {
                        "notification_id": notification_id,
                        "action": action,
                        **data,
                    },
                    "badge": 1,
                    "sound": "default" if prefs.notification_sound else None,
                }

                response = requests.post(
                    EXPO_PUSH_URL,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10,
                )

                if response.status_code == 200:
                    successful_sends += 1
                    logger.info(f"Notification sent to {user.email} on {device.device_type}")
                else:
                    logger.error(f"Expo API error: {response.status_code} - {response.text}")

            except requests.RequestException as e:
                logger.error(f"Error sending notification to {user.email}: {str(e)}")
                continue

        # Save notification record to database
        if successful_sends > 0:
            Notification.objects.create(
                user=user,
                title=title,
                body=body,
                notification_type=notification_type,
                action=action,
                data=data,
            )

        return notification_id if successful_sends > 0 else None

    @staticmethod
    def send_to_users(
        users: List[User],
        title: str,
        body: str,
        notification_type: str = "other",
        action: str = "",
        data: Optional[Dict] = None,
    ) -> Dict[str, int]:
        """
        Send a push notification to multiple users.
        
        Args:
            users: List of User objects
            title: Notification title
            body: Notification body/message
            notification_type: Type of notification
            action: Action type
            data: Additional data
            
        Returns:
            Dictionary with counts of sent notifications
        """
        results = {
            "total": len(users),
            "sent": 0,
            "skipped": 0,
            "failed": 0,
        }

        for user in users:
            try:
                notification_id = NotificationService.send_to_user(
                    user=user,
                    title=title,
                    body=body,
                    notification_type=notification_type,
                    action=action,
                    data=data,
                )
                if notification_id:
                    results["sent"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                logger.error(f"Error sending to user {user.email}: {str(e)}")
                results["failed"] += 1

        return results

    @staticmethod
    def send_sos_alert(
        user: User,
        location_address: str = "",
        location_data: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        Send SOS emergency alert to user and their family.
        
        Args:
            user: User who triggered SOS
            location_address: Current location address
            location_data: Location coordinates and other data
        """
        # Get user's family members
        from family.models import FamilyMember

        family_members = FamilyMember.objects.filter(
            parent_user=user, relation_type__in=['child', 'elderly']
        ).select_related('family_member_user')

        if not family_members.exists():
            logger.warning(f"No family members found for SOS from {user.email}")
            return None

        # Prepare data
        data = {
            "sos_triggered_by": str(user.id),
            "location_address": location_address,
            **(location_data or {}),
        }

        # Send to each family member
        recipients = [fm.family_member_user for fm in family_members]
        
        return NotificationService.send_to_users(
            users=recipients,
            title=f"🚨 SOS Alert: {user.get_full_name()} needs help!",
            body=f"Location: {location_address or 'Unknown'}. Respond immediately.",
            notification_type="sos_alert",
            action="sos_alert",
            data=data,
        )

    @staticmethod
    def send_medication_reminder(
        user: User,
        medication_name: str = "",
        medication_id: Optional[str] = None,
    ) -> Optional[str]:
        """Send medication reminder notification."""
        data = {}
        if medication_id:
            data["medication_id"] = medication_id

        return NotificationService.send_to_user(
            user=user,
            title="💊 Medication Reminder",
            body=f"Time to take {medication_name or 'your medication'}",
            notification_type="medication_reminder",
            action="medication_reminder",
            data=data,
        )

    @staticmethod
    def send_health_update(
        user: User,
        metric_name: str = "Health",
        metric_value: str = "",
        alert_level: str = "info",
    ) -> Optional[str]:
        """Send health update notification."""
        data = {
            "metric_name": metric_name,
            "metric_value": metric_value,
            "alert_level": alert_level,
        }

        title = f"❤️ {metric_name} Update"
        if alert_level == "warning":
            title = f"⚠️ {metric_name} Alert"

        notification_type = "health_update"

        return NotificationService.send_to_user(
            user=user,
            title=title,
            body=f"Your {metric_name} is {metric_value}",
            notification_type=notification_type,
            action="health_update",
            data=data,
        )

    @staticmethod
    def send_appointment_reminder(
        user: User,
        doctor_name: str = "Your doctor",
        appointment_time: str = "",
        appointment_id: Optional[str] = None,
    ) -> Optional[str]:
        """Send appointment reminder notification."""
        data = {}
        if appointment_id:
            data["appointment_id"] = appointment_id

        return NotificationService.send_to_user(
            user=user,
            title="📅 Appointment Reminder",
            body=f"You have an appointment with {doctor_name} at {appointment_time}",
            notification_type="appointment_reminder",
            action="appointment_reminder",
            data=data,
        )

    @staticmethod
    def send_family_message(
        user: User,
        from_user: User,
        message: str = "",
        message_id: Optional[str] = None,
    ) -> Optional[str]:
        """Send family message notification."""
        data = {
            "from_user_id": str(from_user.id),
            "from_user_name": from_user.get_full_name() or from_user.email,
        }
        if message_id:
            data["message_id"] = message_id

        return NotificationService.send_to_user(
            user=user,
            title=f"💬 Message from {from_user.get_full_name() or 'Family'}",
            body=message[:100] if message else "You have a new message",
            notification_type="family_message",
            action="family_message",
            data=data,
        )


# Convenience functions
def send_notification(
    user: User,
    title: str,
    body: str,
    notification_type: str = "other",
    action: str = "",
    data: Optional[Dict] = None,
) -> Optional[str]:
    """Convenience function to send a notification."""
    return NotificationService.send_to_user(
        user=user,
        title=title,
        body=body,
        notification_type=notification_type,
        action=action,
        data=data,
    )


def send_notifications(
    users: List[User],
    title: str,
    body: str,
    notification_type: str = "other",
    action: str = "",
    data: Optional[Dict] = None,
) -> Dict[str, int]:
    """Convenience function to send notifications to multiple users."""
    return NotificationService.send_to_users(
        users=users,
        title=title,
        body=body,
        notification_type=notification_type,
        action=action,
        data=data,
    )
