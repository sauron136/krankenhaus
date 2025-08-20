# pharmacy/models.py
from django.db import models
from django.utils import timezone
from appointments.models import Appointment

class Medication(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    brand_name = models.CharField(max_length=200, blank=True)
    strength = models.CharField(max_length=50)  # e.g., "500mg", "10mg/ml"
    form = models.CharField(max_length=50)  # tablet, capsule, syrup, injection
    manufacturer = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} {self.strength} ({self.form})"

class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='prescriptions_written')
    prescription_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Prescription for {self.patient} by {self.doctor} on {self.prescription_date.date()}"

class PrescriptionItem(models.Model):
   PRESCRIPTION_TYPES = [
       ('outpatient', 'Outpatient - Take Home'),
       ('inpatient', 'Inpatient - Hospital Administration'),
   ]
   
   FREQUENCY_CHOICES = [
       ('once_daily', 'Once Daily'),
       ('twice_daily', 'Twice Daily'),
       ('three_times_daily', 'Three Times Daily'),
       ('four_times_daily', 'Four Times Daily'),
       ('every_4_hours', 'Every 4 Hours'),
       ('every_6_hours', 'Every 6 Hours'),
       ('every_8_hours', 'Every 8 Hours'),
       ('every_12_hours', 'Every 12 Hours'),
       ('as_needed', 'As Needed (PRN)'),
       ('before_meals', 'Before Meals'),
       ('after_meals', 'After Meals'),
       ('bedtime', 'At Bedtime'),
   ]
   
   prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
   medication = models.ForeignKey(Medication, on_delete=models.CASCADE, null=True, blank=True)
   
   # For dynamic medications not in our database
   medication_name = models.CharField(max_length=200, blank=True)
   medication_strength = models.CharField(max_length=50, blank=True)
   medication_form = models.CharField(max_length=50, blank=True)
   
   prescription_type = models.CharField(max_length=20, choices=PRESCRIPTION_TYPES)
   dosage = models.CharField(max_length=100)  # e.g., "1 tablet", "5ml", "2 capsules"
   frequency = models.CharField(max_length=50, choices=FREQUENCY_CHOICES)
   duration_days = models.IntegerField()  # How many days to take
   quantity = models.IntegerField()  # Total quantity to dispense
   refills = models.IntegerField(default=0)  # Number of refills allowed
   
   instructions = models.TextField(blank=True)  # Additional instructions
   start_date = models.DateField(default=timezone.now)
   is_active = models.BooleanField(default=True)
   
   def __str__(self):
       med_name = self.medication.name if self.medication else self.medication_name
       return f"{med_name} - {self.dosage} {self.frequency}"
   
   def get_medication_display(self):
       if self.medication:
           return f"{self.medication.name} {self.medication.strength}"
       else:
           return f"{self.medication_name} {self.medication_strength}"

class PharmacyDispensing(models.Model):
   STATUS_CHOICES = [
       ('pending', 'Pending'),
       ('in_progress', 'In Progress'),
       ('completed', 'Completed'),
       ('cancelled', 'Cancelled'),
       ('on_hold', 'On Hold'),
   ]
   
   prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, related_name='dispensings')
   dispensed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='medications_dispensed')
   dispensed_to = models.CharField(max_length=200)  # Patient name or authorized person
   
   quantity_dispensed = models.IntegerField()
   batch_number = models.CharField(max_length=100, blank=True)
   expiry_date = models.DateField(null=True, blank=True)
   dispensed_at = models.DateTimeField(default=timezone.now)
   
   status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
   notes = models.TextField(blank=True)
   
   def __str__(self):
       return f"Dispensed {self.quantity_dispensed} of {self.prescription_item.get_medication_display()} to {self.dispensed_to}"

class MedicationAdministration(models.Model):
   STATUS_CHOICES = [
       ('scheduled', 'Scheduled'),
       ('administered', 'Administered'),
       ('refused', 'Patient Refused'),
       ('missed', 'Missed'),
       ('cancelled', 'Cancelled'),
   ]
   
   prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, related_name='administrations')
   patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='medication_administrations')
   administered_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='medications_administered', null=True, blank=True)
   
   scheduled_time = models.DateTimeField()
   actual_time = models.DateTimeField(null=True, blank=True)
   dose_given = models.CharField(max_length=100)
   
   status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
   notes = models.TextField(blank=True)
   
   created_at = models.DateTimeField(auto_now_add=True)
   updated_at = models.DateTimeField(auto_now=True)
   
   def __str__(self):
       return f"{self.prescription_item.get_medication_display()} for {self.patient} at {self.scheduled_time}"
   
   class Meta:
       ordering = ['scheduled_time']
