from django.core.management.base import BaseCommand
from accounts.models import Role

class Command(BaseCommand):
    help = 'Create default roles for hospital management system'
    
    def handle(self, *args, **options):
        roles_data = [
            {
                'name': 'Doctor',
                'description': 'Medical doctor with full patient care access',
                'access_level': 'senior_medical',
                'can_trigger_emergency': True
            },
            {
                'name': 'Specialist',
                'description': 'Medical specialist with full patient care access',
                'access_level': 'senior_medical',
                'can_trigger_emergency': True
            },
            {
                'name': 'Senior Doctor',
                'description': 'Senior medical doctor with emergency override capabilities',
                'access_level': 'emergency',
                'can_trigger_emergency': True
            },
            {
                'name': 'Nurse',
                'description': 'Registered nurse with medical access',
                'access_level': 'medical',
                'can_trigger_emergency': False
            },
            {
                'name': 'Pharmacist',
                'description': 'Licensed pharmacist with prescription access',
                'access_level': 'medical',
                'can_trigger_emergency': False
            },
            {
                'name': 'Lab Technician',
                'description': 'Laboratory technician with lab test access',
                'access_level': 'medical',
                'can_trigger_emergency': False
            },
            {
                'name': 'Receptionist',
                'description': 'Front desk receptionist with basic patient info access',
                'access_level': 'basic',
                'can_trigger_emergency': False
            },
            {
                'name': 'Admin',
                'description': 'System administrator with full system access',
                'access_level': 'administrative',
                'can_trigger_emergency': False
            },
