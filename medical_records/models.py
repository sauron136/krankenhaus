from django.db import models

from .managers import MedicalRecordManager, DiagnosisManager, AllergyManager  # Import managers

class MedicalRecord(models.Model):
    objects = MedicalRecordManager()  # Assign the custom manager

    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='medical_records')
    created_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True)
    
    # Visit Information
    visit_type = models.CharField(max_length=50, choices=[
        ('consultation', 'Consultation'),
        ('emergency', 'Emergency'),
        ('follow_up', 'Follow-up'),
        ('routine_checkup', 'Routine Checkup'),
        ('surgery', 'Surgery'),
    ])
    chief_complaint = models.TextField(blank=True)
    
    # Vital Signs
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    oxygen_saturation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Clinical Notes
    history_of_present_illness = models.TextField(blank=True)
    physical_examination = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.patient_id} - {self.visit_type} on {self.created_at.date()}"

class Diagnosis(models.Model):
    objects = DiagnosisManager()  # Assign the custom manager

    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='diagnoses')
    icd_10_code = models.CharField(max_length=20, blank=True)
    diagnosis_description = models.TextField()
    diagnosis_type = models.CharField(max_length=20, choices=[
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('provisional', 'Provisional'),
        ('differential', 'Differential'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ], blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.diagnosis_description} ({self.diagnosis_type})"

class Allergy(models.Model):
    objects = AllergyManager()  # Assign the custom manager

    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='allergies')
    allergen = models.CharField(max_length=200)
    allergy_type = models.CharField(max_length=50, choices=[
        ('drug', 'Drug/Medication'),
        ('food', 'Food'),
        ('environmental', 'Environmental'),
        ('contact', 'Contact'),
        ('other', 'Other'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('anaphylactic', 'Anaphylactic'),
    ])
    reaction_description = models.TextField()
    onset_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.patient.patient_id} - {self.allergen} ({self.severity})"
