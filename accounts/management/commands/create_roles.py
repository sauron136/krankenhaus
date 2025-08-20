from django.core.management.base import BaseCommand
from accounts.models import Role

class Command(BaseCommand):
    help = 'Create default hospital roles'
    
    def handle(self, *args, **options):
        roles = [
            {'name': 'Doctor', 'description': 'Medical doctor providing patient care'},
            {'name': 'Nurse', 'description': 'Registered nurse providing patient care'},
            {'name': 'ICU_Nurse', 'description': 'Intensive Care Unit nurse'},
            {'name': 'Emergency_Nurse', 'description': 'Emergency department nurse'},
            {'name': 'Pediatric_Nurse', 'description': 'Pediatric care nurse'},
            {'name': 'OR_Nurse', 'description': 'Operating room nurse'},
            {'name': 'Lab_Technician', 'description': 'Laboratory technician'},
            {'name': 'Radiologist', 'description': 'Medical imaging specialist'},
            {'name': 'Pharmacist', 'description': 'Hospital pharmacist'},
            {'name': 'Administrative_Staff', 'description': 'Administrative personnel'},
            {'name': 'HR_Manager', 'description': 'Human Resources manager'},
            {'name': 'Department_Head', 'description': 'Department head/supervisor'},
            {'name': 'Security_Guard', 'description': 'Hospital security personnel'},
            {'name': 'Maintenance_Staff', 'description': 'Hospital maintenance personnel'},
            {'name': 'Midwife', 'description': 'Certified midwife'},
            {'name': 'Anesthesiologist', 'description': 'Anesthesia specialist'},
            {'name': 'Surgeon', 'description': 'Surgical specialist'},
            {'name': 'Cardiologist', 'description': 'Heart specialist'},
            {'name': 'Neurologist', 'description': 'Nervous system specialist'},
            {'name': 'Pediatrician', 'description': 'Children healthcare specialist'},
            {'name': 'Admin', 'description': 'System administrator'},
        ]
        
        created_count = 0
        for role_data in roles:
            role, created = Role.objects.get_or_create(
                name=role_data['name'],
                defaults={'description': role_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created role: {role.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Role already exists: {role.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new roles')
        )
