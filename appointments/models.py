from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import Personnel, Patient

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class AppointmentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.duration_minutes}min)"

class ProviderAvailability(models.Model):
    """Defines when medical providers are available for appointments"""
    DAYS_OF_WEEK = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    provider = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['provider', 'day_of_week', 'start_time']
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
    
    def __str__(self):
        return f"{self.provider} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    provider = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='provider_appointments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='appointments')
    appointment_type = models.ForeignKey(AppointmentType, on_delete=models.CASCADE)
    
    # Appointment timing
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Additional details
    reason_for_visit = models.TextField()
    notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Tracking
    created_by = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, related_name='created_appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Follow-up
    is_follow_up = models.BooleanField(default=False)
    parent_appointment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='follow_ups')
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'appointment_time']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['provider', 'appointment_date']),
        ]
    
    def clean(self):
        # Ensure appointment is in the future (except for walk-ins)
        appointment_datetime = timezone.datetime.combine(self.appointment_date, self.appointment_time)
        if appointment_datetime <= timezone.now() and self.status == 'scheduled':
            raise ValidationError("Appointment must be scheduled for a future date/time")
        
        # Set duration from appointment type if not specified
        if not self.duration_minutes and self.appointment_type:
            self.duration_minutes = self.appointment_type.duration_minutes
    
    @property
    def appointment_datetime(self):
        return timezone.datetime.combine(self.appointment_date, self.appointment_time)
    
    @property
    def end_time(self):
        return (self.appointment_datetime + timezone.timedelta(minutes=self.duration_minutes)).time()
    
    def __str__(self):
        return f"{self.patient} with {self.provider} on {self.appointment_date} at {self.appointment_time}"

class AppointmentStatusHistory(models.Model):
    """Track status changes for appointments"""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    changed_by = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True)
    reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.appointment} - {self.old_status} to {self.new_status}"
