from django.db import models
from django.utils import timezone
from django.db.models import Q  # Added for potential future query expansions

class AppointmentManager(models.Manager):
    def upcoming_appointments(self):
        """Get upcoming appointments"""
        return self.filter(
            scheduled_date__gte=timezone.now().date(),
            status__in=['scheduled', 'confirmed']
        )
    
    def today_appointments(self):
        """Get today's appointments"""
        today = timezone.now().date()
        return self.filter(scheduled_date=today)
    
    def for_patient(self, patient):
        """Get appointments for specific patient"""
        return self.filter(patient=patient).order_by('scheduled_date', 'scheduled_time')
    
    def for_doctor(self, doctor):
        """Get appointments for specific doctor"""
        return self.filter(doctor=doctor).order_by('scheduled_date', 'scheduled_time')
    
    def by_status(self, status):
        """Get appointments by status"""
        return self.filter(status=status)
    
    def cancelled_appointments(self):
        """Get cancelled appointments"""
        return self.filter(status='cancelled')
    
    def completed_appointments(self):
        """Get completed appointments"""
        return self.filter(status='completed')
    
    def no_show_appointments(self):
        """Get no-show appointments"""
        return self.filter(status='no_show')
