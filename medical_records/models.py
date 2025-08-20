from django.db import models
from django.utils import timezone
from appointments.models import Appointment

class MedicalRecord(models.Model):
    """Main patient medical record - one per patient"""
    patient = models.OneToOneField('accounts.Patient', on_delete=models.CASCADE, related_name='medical_record')
    blood_type = models.CharField(max_length=5, blank=True)  # A+, B-, O+, etc.
    emergency_contact = models.TextField(blank=True)
    insurance_info = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Medical Record - {self.patient.get_full_name()}"

class Allergy(models.Model):
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('life_threatening', 'Life Threatening'),
    ]
    
    ALLERGY_TYPES = [
        ('drug', 'Drug/Medication'),
        ('food', 'Food'),
        ('environmental', 'Environmental'),
        ('latex', 'Latex'),
        ('other', 'Other'),
    ]
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='allergies')
    allergen = models.CharField(max_length=200)
    allergy_type = models.CharField(max_length=20, choices=ALLERGY_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    reaction = models.TextField()  # What happens when exposed
    
    date_identified = models.DateField(default=timezone.now)
    identified_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.allergen} - {self.severity}"
    
    class Meta:
        unique_together = ['medical_record', 'allergen']

class MedicalHistory(models.Model):
    """Past medical conditions, surgeries, etc."""
    CONDITION_TYPES = [
        ('chronic_condition', 'Chronic Condition'),
        ('past_surgery', 'Past Surgery'),
        ('past_hospitalization', 'Past Hospitalization'),
        ('family_history', 'Family History'),
        ('social_history', 'Social History'),
        ('other', 'Other'),
    ]
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='medical_history')
    condition_type = models.CharField(max_length=30, choices=CONDITION_TYPES)
    condition = models.CharField(max_length=300)
    icd_code = models.CharField(max_length=20, blank=True)  # ICD-10 code
    
    date_occurred = models.DateField(null=True, blank=True)
    date_resolved = models.DateField(null=True, blank=True)
    
    description = models.TextField(blank=True)
    is_ongoing = models.BooleanField(default=False)
    
    recorded_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.condition} - {self.condition_type}"

class Encounter(models.Model):
    """Each patient visit/appointment creates an encounter"""
    ENCOUNTER_TYPES = [
        ('outpatient', 'Outpatient Visit'),
        ('inpatient', 'Inpatient Admission'),
        ('emergency', 'Emergency Visit'),
        ('surgery', 'Surgery'),
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('telemedicine', 'Telemedicine'),
    ]
    
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='encounters')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='encounter', null=True, blank=True)
    
    encounter_type = models.CharField(max_length=20, choices=ENCOUNTER_TYPES)
    encounter_date = models.DateTimeField(default=timezone.now)
    
    provider = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='encounters_provided')
    department = models.ForeignKey('appointments.Department', on_delete=models.SET_NULL, null=True, blank=True)
    
    chief_complaint = models.TextField()  # Why patient came in
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Encounter - {self.medical_record.patient.get_full_name()} - {self.encounter_date.date()}"
    
    class Meta:
        ordering = ['-encounter_date']

class VitalSigns(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='vital_signs')
    
    systolic_bp = models.IntegerField(null=True, blank=True)  # mmHg
    diastolic_bp = models.IntegerField(null=True, blank=True)  # mmHg
    heart_rate = models.IntegerField(null=True, blank=True)  # bpm
    respiratory_rate = models.IntegerField(null=True, blank=True)  # breaths/min
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)  # Celsius
    oxygen_saturation = models.IntegerField(null=True, blank=True)  # %
    
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # kg
    bmi = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    
    pain_score = models.IntegerField(null=True, blank=True)  # 0-10 scale
    
    recorded_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='vitals_recorded')
    recorded_at = models.DateTimeField(default=timezone.now)
    
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # Auto-calculate BMI if height and weight are provided
        if self.height and self.weight:
            height_m = float(self.height) / 100  # Convert cm to meters
            self.bmi = round(float(self.weight) / (height_m * height_m), 1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Vitals - {self.encounter.medical_record.patient.get_full_name()} - {self.recorded_at.date()}"

class ClinicalNote(models.Model):
    NOTE_TYPES = [
        ('history_physical', 'History & Physical'),
        ('progress_note', 'Progress Note'),
        ('consultation', 'Consultation Note'),
        ('discharge_summary', 'Discharge Summary'),
        ('operative_note', 'Operative Note'),
        ('nursing_note', 'Nursing Note'),
        ('assessment_plan', 'Assessment & Plan'),
        ('other', 'Other'),
    ]
    
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='clinical_notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES)
    
    subjective = models.TextField(blank=True)  # Patient's complaints/symptoms (SOAP format)
    objective = models.TextField(blank=True)  # Observable findings
    assessment = models.TextField(blank=True)  # Clinical impression/diagnosis
    plan = models.TextField(blank=True)  # Treatment plan
    
    additional_notes = models.TextField(blank=True)
    
    author = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='clinical_notes_authored')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.note_type} - {self.encounter.medical_record.patient.get_full_name()} - {self.created_at.date()}"
    
    class Meta:
        ordering = ['-created_at']

class Diagnosis(models.Model):
    DIAGNOSIS_TYPES = [
        ('primary', 'Primary Diagnosis'),
        ('secondary', 'Secondary Diagnosis'),
        ('differential', 'Differential Diagnosis'),
        ('rule_out', 'Rule Out'),
    ]
    
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_type = models.CharField(max_length=20, choices=DIAGNOSIS_TYPES)
    
    condition = models.CharField(max_length=300)
    icd_10_code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    
    diagnosed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='diagnoses_made')
    diagnosis_date = models.DateTimeField(default=timezone.now)
    
    is_active = models.BooleanField(default=True)
    resolved_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.condition} ({self.diagnosis_type})"

class TreatmentPlan(models.Model):
    PLAN_TYPES = [
        ('medication', 'Medication'),
        ('procedure', 'Procedure'),
        ('therapy', 'Therapy'),
        ('surgery', 'Surgery'),
        ('follow_up', 'Follow-up'),
        ('referral', 'Referral'),
        ('lifestyle', 'Lifestyle Modification'),
        ('monitoring', 'Monitoring'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='treatment_plans')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    
    description = models.TextField()
    instructions = models.TextField(blank=True)
    
    start_date = models.DateField(default=timezone.now)
    target_completion_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    prescribed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='treatment_plans_prescribed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.plan_type}: {self.description[:50]}..."

class RecordAccess(models.Model):
    """Track who accessed which records for audit purposes"""
    medical_record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='access_logs')
    accessed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='record_accesses')
    
    access_type = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('edit', 'Edit'),
        ('create', 'Create'),
        ('delete', 'Delete'),
    ])
    
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.accessed_by} {self.access_type} {self.medical_record.patient.get_full_name()} at {self.accessed_at}"
