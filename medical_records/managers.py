from django.db import models
from django.utils import timezone
from django.db.models import Q  # Added for Q objects in for_patient

class MedicalRecordManager(models.Manager):
    def for_patient(self, patient):
        """Get all medical records for a patient"""
        return self.filter(patient=patient).order_by('-created_at')
    
    def by_visit_type(self, visit_type):
        """Get records by visit type"""
        return self.filter(visit_type=visit_type)
    
    def emergency_visits(self):
        """Get emergency visit records"""
        return self.filter(visit_type='emergency')
    
    def recent_records(self, days=30):
        """Get recent medical records"""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def by_doctor(self, doctor):
        """Get records created by specific doctor"""
        return self.filter(created_by=doctor)


class DiagnosisManager(models.Manager):
    def primary_diagnoses(self):
        """Get primary diagnoses only"""
        return self.filter(diagnosis_type='primary')
    
    def by_icd10(self, icd_code):
        """Get diagnoses by ICD-10 code"""
        return self.filter(icd_10_code=icd_code)
    
    def critical_diagnoses(self):
        """Get critical severity diagnoses"""
        return self.filter(severity='critical')
    
    def for_patient(self, patient):
        """Get all diagnoses for a patient"""
        return self.filter(medical_record__patient=patient)


class AllergyManager(models.Manager):
    def active_allergies(self):
        """Get active allergies only"""
        return self.filter(is_active=True)
    
    def for_patient(self, patient):
        """Get active allergies for a patient"""
        return self.filter(patient=patient, is_active=True)
    
    def drug_allergies(self):
        """Get drug/medication allergies"""
        return self.filter(allergy_type='drug', is_active=True)
    
    def severe_allergies(self):
        """Get severe and anaphylactic allergies"""
        return self.filter(severity__in=['severe', 'anaphylactic'], is_active=True)
    
    def by_allergen(self, allergen):
        """Get allergies by specific allergen"""
        return self.filter(allergen__icontains=allergen, is_active=True)
