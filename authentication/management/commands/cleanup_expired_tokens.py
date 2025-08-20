from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import CustomJWTToken, OTPToken

class Command(BaseCommand):
    help = 'Clean up expired JWT tokens and OTP tokens'
    
    def handle(self, *args, **options):
        now = timezone.now()
        
        # Clean up expired JWT tokens
        expired_jwt_count = CustomJWTToken.objects.filter(expires_at__lt=now).delete()[0]
        
        # Clean up expired OTP tokens
        expired_otp_count = OTPToken.objects.filter(expires_at__lt=now).delete()[0]
        
        # Clean up used OTP tokens older than 24 hours
        yesterday = now - timezone.timedelta(days=1)
        old_used_otp_count = OTPToken.objects.filter(
            is_used=True, 
            created_at__lt=yesterday
        ).delete()[0]
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Cleaned up {expired_jwt_count} expired JWT tokens, '
                f'{expired_otp_count} expired OTP tokens, '
                f'and {old_used_otp_count} old used OTP tokens'
            )
        )
