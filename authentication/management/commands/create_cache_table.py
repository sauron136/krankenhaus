from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Create cache table for JWT token blacklist'
    
    def handle(self, *args, **options):
        try:
            call_command('createcachetable', 'jwt_cache_table')
            self.stdout.write(
                self.style.SUCCESS('Successfully created cache table for JWT blacklist')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create cache table: {str(e)}')
            )
