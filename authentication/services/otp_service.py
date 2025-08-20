import random
import string
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from ..models import OTPToken

class OTPService:
    
    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp(cls, user, otp_type, request=None):
        otp_code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)  # 10 min expiry
        
        # Deactivate previous OTPs of same type for user
        if hasattr(user, 'otp_tokens'):
            user.otp_tokens.filter(otp_type=otp_type, is_used=False).update(is_used=True)
        
        # Determine user type
        is_personnel = hasattr(user, 'username')  # Personnel has username
        
        # Get IP if request provided
        ip_address = None
        if request:
            ip_address = cls.get_client_ip(request)
        
        otp_token = OTPToken.objects.create(
            personnel=user if is_personnel else None,
            patient=user if not is_personnel else None,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at,
            ip_address=ip_address
        )
        
        return otp_token
    
    @classmethod
    def verify_otp(cls, user, otp_code, otp_type):
        try:
            # Determine user type
            is_personnel = hasattr(user, 'username')
            
            otp_token = OTPToken.objects.get(
                personnel=user if is_personnel else None,
                patient=user if not is_personnel else None,
                otp_code=otp_code,
                otp_type=otp_type,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            
            otp_token.is_used = True
            otp_token.save()
            return True
            
        except OTPToken.DoesNotExist:
            return False
    
    @classmethod
    def send_otp_email(cls, user, otp_code, otp_type):
        subject_map = {
            'email_verification': 'Verify Your Email - Hospital System',
            'password_reset': 'Password Reset Code - Hospital System',
            'login_verification': 'Login Verification Code - Hospital System',
            'account_unlock': 'Account Unlock Code - Hospital System',
        }
        
        subject = subject_map.get(otp_type, 'OTP Code - Hospital System')
        message = f'Your verification code is: {otp_code}\nThis code expires in 10 minutes.'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
