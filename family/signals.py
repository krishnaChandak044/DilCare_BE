"""
Family signals — Handle notifications for family events
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FamilyMembership
from accounts.services import NotificationService


@receiver(post_save, sender=FamilyMembership)
def notify_family_on_new_member(sender, instance, created, **kwargs):
    """
    Send notification to all family members when a new member joins
    """
    if not created:
        return
    
    try:
        # Get all members of this family (excluding the new member)
        family = instance.family
        other_members = family.members.exclude(id=instance.user.id).values_list('id', flat=True)
        
        if not other_members.exists():
            return
        
        # Prepare notification
        user_name = f"{instance.user.first_name} {instance.user.last_name}".strip() or instance.user.email
        title = "New Family Member"
        body = f"{user_name} has joined the {family.name or 'family'}!"
        
        # Send to all existing family members
        NotificationService.send_to_users(
            user_ids=list(other_members),
            title=title,
            body=body,
            data={
                'action': 'family_member_joined',
                'new_member_id': str(instance.user.id),
                'new_member_name': user_name,
                'family_id': str(family.id),
                'family_name': family.name,
            }
        )
    except Exception as e:
        # Log but don't fail the operation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error sending family member notification: {e}")
