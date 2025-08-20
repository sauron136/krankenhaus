from django.core.management.base import BaseCommand
from appointments.models import Department, AppointmentType

class Command(BaseCommand):
    help = 'Set up default departments and appointment types'
    
    def handle(self, *args, **options):
        # Create departments
        departments = [
            {'name': 'Emergency', 'description': 'Emergency department for urgent care'},
            {'name': 'Cardiology', 'description': 'Heart and cardiovascular care'},
            {'name': 'Orthopedics', 'description': 'Bone, joint, and muscle care'},
            {'name': 'Pediatrics', 'description': 'Healthcare for children'},
            {'name': 'Neurology', 'description': 'Nervous system care'},
            {'name': 'Radiology', 'description': 'Medical imaging services'},
            {'name': 'Laboratory', 'description': 'Laboratory testing and analysis'},
            {'name': 'Surgery', 'description': 'Surgical procedures'},
            {'name': 'Internal Medicine', 'description': 'General internal medicine'},
            {'name': 'Obstetrics and Gynecology', 'description': 'Women\'s health and pregnancy care'},
        ]
        
        dept_created = 0
        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                dept_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created department: {dept.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Department already exists: {dept.name}')
                )
        
        # Create appointment types
        appointment_types = [
            {'name': 'Consultation', 'description': 'General consultation with doctor', 'duration_minutes': 30},
            {'name': 'Follow-up', 'description': 'Follow-up appointment', 'duration_minutes': 15},
            {'name': 'Emergency', 'description': 'Emergency appointment', 'duration_minutes': 60},
            {'name': 'Surgery Consultation', 'description': 'Pre-surgery consultation', 'duration_minutes': 45},
            {'name': 'Lab Test', 'description': 'Laboratory testing appointment', 'duration_minutes': 15},
            {'name': 'Imaging', 'description': 'Medical imaging appointment', 'duration_minutes': 30},
            {'name': 'Physical Therapy', 'description': 'Physical therapy session', 'duration_minutes': 45},
            {'name': 'Vaccination', 'description': 'Vaccination appointment', 'duration_minutes': 15},
            {'name': 'Health Checkup', 'description': 'Routine health checkup', 'duration_minutes': 45},
            {'name': 'Specialist Consultation', 'description': 'Consultation with specialist', 'duration_minutes': 45},
        ]
        
        appt_created = 0
        for appt_data in appointment_types:
            appt_type, created = AppointmentType.objects.get_or_create(
                name=appt_data['name'],
                defaults={
                    'description': appt_data['description'],
                    'duration_minutes': appt_data['duration_minutes']
                }
            )
            if created:
                appt_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created appointment type: {appt_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Appointment type already exists: {appt_type.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {dept_created} departments and {appt_created} appointment types'
            )
        )
