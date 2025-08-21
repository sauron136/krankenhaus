from django.db import models

from .managers import AppointmentManager  # Import the manager

class Appointment(models.Model):
    objects = AppointmentManager()  # Assign the custom manager

    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='doctor_appointments')
    
    appointment_type = models.CharField(max_length=50, choices=[
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('routine_checkup', 'Routine Checkup'),
        ('urgent_care', 'Urgent Care'),
        ('procedure', 'Procedure'),
    ])
    
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)
    
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ], default='scheduled')
    
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True, related_name='created_appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.patient_id} with Dr. {self.doctor.user.last_name} on {self.scheduled_date}"
