from django.db import models
from django.utils import timezone
from django.db.models import Q
import random
import string

class PatientManager(models.Manager):
    def create_patient_profile(self, user, registration_type='online', registered_by=None, **extra_fields):
        """Create a patient profile for a user"""
        patient = self.model(
            user=user,
            registration_type=registration_type,
            registered_by=registered_by,
            **extra_fields
        )
        patient.save(using=self._db)
        return patient
    
    def get_by_patient_id(self, patient_id):
        """Get patient by their unique patient ID"""
        try:
            return self.get(patient_id=patient_id)
        except self.model.DoesNotExist:
            return None
    
    def search_patients(self, query):
        """Search patients by name, phone, or patient ID"""
        return self.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone_primary__icontains=query) |
            Q(user__email__icontains=query)
        ).select_related('user')
    
    def complete_profiles(self):
        """Get patients with complete profiles"""
        return self.filter(is_profile_complete=True)
    
    def incomplete_profiles(self):
        """Get patients with incomplete profiles"""
        return self.filter(is_profile_complete=False)
    
    def online_registered(self):
        """Get patients who registered online"""
        return self.filter(registration_type='online')
    
    def walk_in_registered(self):
        """Get patients who were registered as walk-ins"""
        return self.filter(registration_type='walk_in')
    
    def emergency_search(self, first_name, last_name, date_of_birth=None, phone=None):
        """Emergency search for patients when ID is not available"""
        query = self.filter(
            user__first_name__iexact=first_name,
            user__last_name__iexact=last_name
        ).select_related('user')
        
        if date_of_birth:
            query = query.filter(date_of_birth=date_of_birth)
        
        if phone:
            query = query.filter(
                Q(phone_primary=phone) | Q(phone_secondary=phone)
            )
        
        return query


class PersonnelManager(models.Manager):
    def create_personnel_profile(self, user, **extra_fields):
        """Create a personnel profile for a user"""
        # Generate employee ID if not provided
        if 'employee_id' not in extra_fields:
            extra_fields['employee_id'] = self._generate_employee_id()
        
        personnel = self.model(user=user, **extra_fields)
        personnel.save(using=self._db)
        return personnel
    
    def _generate_employee_id(self):
        """Generate a unique employee ID"""
        while True:
            year = timezone.now().year
            random_part = ''.join(random.choices(string.digits, k=4))
            employee_id = f"EMP{year}{random_part}"
            
            if not self.filter(employee_id=employee_id).exists():
                return employee_id
    
    def verified_personnel(self):
        """Get verified personnel only"""
        return self.filter(is_verified=True, is_active=True)
    
    def pending_verification(self):
        """Get personnel pending verification"""
        return self.filter(verification_status='pending', is_active=True)
    
    def in_review_verification(self):
        """Get personnel in review process"""
        return self.filter(verification_status='in_review', is_active=True)
    
    def rejected_verification(self):
        """Get personnel with rejected verification"""
        return self.filter(verification_status='rejected', is_active=True)
    
    def by_role(self, role_name):
        """Get personnel by role name"""
        return self.filter(
            role_assignments__role__name=role_name,
            role_assignments__is_active=True,
            is_active=True
        ).distinct()
    
    def doctors(self):
        """Get all doctors (including specialists)"""
        return self.filter(
            role_assignments__role__name__in=['Doctor', 'Specialist', 'Senior Doctor'],
            role_assignments__is_active=True,
            is_verified=True,
            is_active=True
        ).distinct()
    
    def emergency_override_capable(self):
        """Get personnel who can trigger emergency overrides"""
        return self.filter(
            role_assignments__role__can_trigger_emergency=True,
            role_assignments__is_active=True,
            is_verified=True,
            is_active=True
        ).distinct()
    
    def by_department(self, department):
        """Get personnel by department"""
        return self.filter(department=department, is_active=True)
    
    def supervisors(self):
        """Get personnel who supervise others"""
        return self.filter(supervised_staff__isnull=False).distinct()
    
    def search_personnel(self, query):
        """Search personnel by name, employee ID, or email"""
        return self.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(user__email__icontains=query)
        ).select_related('user')


class RoleManager(models.Manager):
    def medical_roles(self):
        """Get roles with medical access"""
        return self.filter(access_level__in=['medical', 'senior_medical'])
    
    def administrative_roles(self):
        """Get administrative roles"""
        return self.filter(access_level='administrative')
    
    def emergency_capable_roles(self):
        """Get roles that can trigger emergency overrides"""
        return self.filter(can_trigger_emergency=True)
    
    def basic_access_roles(self):
        """Get roles with basic access only"""
        return self.filter(access_level='basic')


class PersonnelRoleManager(models.Manager):
    def active_assignments(self):
        """Get active role assignments only"""
        return self.filter(is_active=True)
    
    def expired_assignments(self):
        """Get expired role assignments"""
        return self.filter(
            expires_date__lt=timezone.now(),
            is_active=True
        )
    
    def by_personnel(self, personnel):
        """Get active role assignments for specific personnel"""
        return self.filter(personnel=personnel, is_active=True)
    
    def by_role(self, role):
        """Get active assignments for specific role"""
        return self.filter(role=role, is_active=True)


class EmergencyAccessManager(models.Manager):
    def active_sessions(self):
        """Get active emergency access sessions"""
        return self.filter(session_ended_at__isnull=True)
    
    def by_patient(self, patient):
        """Get emergency access records for a specific patient"""
        return self.filter(patient=patient).order_by('-accessed_at')
    
    def by_personnel(self, personnel):
        """Get emergency access records by personnel"""
        return self.filter(accessed_by=personnel).order_by('-accessed_at')
    
    def today_accesses(self):
        """Get emergency accesses from today"""
        today = timezone.now().date()
        return self.filter(accessed_at__date=today)
    
    def log_emergency_access(self, personnel, patient, reason, access_type='full_override', ip_address=None):
        """Log an emergency access event"""
        return self.create(
            accessed_by=personnel,
            patient=patient,
            reason=reason,
            access_type=access_type,
            ip_address=ip_address or '127.0.0.1'
        )
