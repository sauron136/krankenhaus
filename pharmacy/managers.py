from django.db import models
from django.utils import timezone
from django.db.models import Q  # Added for search_medications

class PrescriptionManager(models.Manager):
    def active_prescriptions(self):
        """Get active prescriptions"""
        return self.filter(status='active')
    
    def for_patient(self, patient):
        """Get prescriptions for specific patient"""
        return self.filter(patient=patient).order_by('-date_prescribed')
    
    def by_doctor(self, doctor):
        """Get prescriptions written by specific doctor"""
        return self.filter(prescribed_by=doctor).order_by('-date_prescribed')
    
    def pending_fill(self):
        """Get prescriptions that need to be filled"""
        return self.filter(status='active')
    
    def filled_prescriptions(self):
        """Get filled prescriptions"""
        return self.filter(status='filled')


class MedicationManager(models.Manager):
    def active_medications(self):
        """Get active medications"""
        return self.filter(is_active=True)
    
    def controlled_substances(self):
        """Get controlled substance medications"""
        return self.filter(is_controlled_substance=True, is_active=True)
    
    def by_generic_name(self, generic_name):
        """Get medications by generic name"""
        return self.filter(generic_name__icontains=generic_name, is_active=True)
    
    def search_medications(self, query):
        """Search medications by name"""
        return self.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(brand_name__icontains=query),
            is_active=True
        )
