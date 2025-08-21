from django.db import models

from .managers import MedicationManager, PrescriptionManager  # Import managers

class Medication(models.Model):
    objects = MedicationManager()  # Assign the custom manager

    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_name = models.CharField(max_length=200, blank=True)
    dosage_form = models.CharField(max_length=100)
    strength = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=200, blank=True)
    ndc_number = models.CharField(max_length=20, blank=True)
    is_controlled_substance = models.BooleanField(default=False)
    controlled_substance_schedule = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.strength})"

class Prescription(models.Model):
    objects = PrescriptionManager()  # Assign the custom manager

    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    prescribed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='prescriptions_written')
    medical_record = models.ForeignKey('medical_records.MedicalRecord', on_delete=models.CASCADE, related_name='prescriptions')
    
    prescription_number = models.CharField(max_length=50, unique=True)
    date_prescribed = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('filled', 'Filled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], default='active')
    
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Prescription {self.prescription_number} for {self.patient.patient_id}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration_days = models.IntegerField()
    quantity = models.IntegerField()
    refills_remaining = models.IntegerField(default=0)
    
    instructions = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.medication.name} - {self.dosage}"

class PharmacyDispensing(models.Model):
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, related_name='dispensing_records')
    dispensed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='dispensed_medications')
    
    quantity_dispensed = models.IntegerField()
    date_dispensed = models.DateTimeField(auto_now_add=True)
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Dispensed {self.quantity_dispensed} of {self.prescription_item.medication.name}"
