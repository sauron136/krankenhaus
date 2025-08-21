from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from accounts.models import Patient, Personnel
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """Handle user creation events"""
    if created:
        logger.info(f"New user created: {instance.email} ({instance.id})")
        
        # You can add additional logic here if needed
        # For example, sending welcome emails, creating default settings, etc.

@receiver(post_save, sender=Patient)
def patient_profile_created_handler(sender, instance, created, **kwargs):
    """Handle patient profile creation"""
    if created:
        logger.info(f"New patient profile created: {instance.patient_id} for user {instance.user.email}")

@receiver(post_save, sender=Personnel)
def personnel_profile_created_handler(sender, instance, created, **kwargs):
    """Handle personnel profile creation"""
    if created:
        logger.info(f"New personnel profile created: {instance.employee_id} for user {instance.user.email}")

@receiver(pre_delete, sender=User)
def user_deletion_handler(sender, instance, **kwargs):
    """Handle user deletion events"""
    logger.warning(f"User being deleted: {instance.email} ({instance.id})")

