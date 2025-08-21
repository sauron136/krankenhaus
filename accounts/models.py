from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string

from .managers import PatientManager, PersonnelManager, RoleManager, PersonnelRoleManager, EmergencyAccessManager  # Import managers

def generate_patient_id():
    year = timezone.now().year
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"HMS{year}{random_part}"

class Patient(models.Model):
    objects = PatientManager()  # Assign the custom manager

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    patient_id = models.CharField(max_length=20, unique=True, default=generate_patient_id)
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], blank=True)
    blood_type = models.CharField(max_length=5, choices=[
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ], blank=True)
    
    # Contact Information
    phone_primary = models.CharField(max_length=20, blank=True)
    phone_secondary = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True)
    
    # Insurance Information
    insurance_provider = models.CharField(max_length=200, blank=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True)
    insurance_group_number = models.CharField(max_length=100, blank=True)
    
    # Registration Details
    registration_type = models.CharField(max_length=20, choices=[
        ('online', 'Online Registration'),
        ('walk_in', 'Walk-in Registration'),
    ], default='online')
    registered_by = models.ForeignKey('Personnel', on_delete=models.SET_NULL, null=True, blank=True, related_name='registered_patients')
    is_profile_complete = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.patient_id})"

class Personnel(models.Model):
    objects = PersonnelManager()  # Assign the custom manager

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personnel_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    phone_work = models.CharField(max_length=20, blank=True)
    phone_personal = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Employment Details
    hire_date = models.DateField(null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True)
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_staff')
    
    # Verification Status
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('in_review', 'In Review'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ], default='pending')
    license_number = models.CharField(max_length=100, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_personnel')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.employee_id})"

class Role(models.Model):
    objects = RoleManager()  # Assign the custom manager

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    access_level = models.CharField(max_length=20, choices=[
        ('basic', 'Basic Access'),
        ('medical', 'Medical Access'),
        ('senior_medical', 'Senior Medical Access'),
        ('administrative', 'Administrative Access'),
        ('emergency', 'Emergency Override Access'),
    ])
    can_trigger_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class PersonnelRole(models.Model):
    objects = PersonnelRoleManager()  # Assign the custom manager

    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, related_name='roles_assigned')
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['personnel', 'role']

class Department(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True, related_name='departments_headed')
    location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class EmergencyAccess(models.Model):
    objects = EmergencyAccessManager()  # Assign the custom manager

    accessed_by = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='emergency_accesses')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_accesses')
    reason = models.TextField()
    access_type = models.CharField(max_length=50, choices=[
        ('full_override', 'Full Override'),
        ('critical_info', 'Critical Information Only'),
    ])
    accessed_at = models.DateTimeField(auto_now_add=True)
    session_ended_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    
    def __str__(self):
        return f"Emergency access by {self.accessed_by} for {self.patient.patient_id}"
