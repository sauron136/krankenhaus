from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random
import string

def generate_otp(length=6):
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp_code, purpose='verification'):
    """Send OTP email with proper template"""
    
    subject_templates = {
        'verification': 'Hospital Management System - Email Verification',
        'password_reset': 'Hospital Management System - Password Reset',
        'login_verification': 'Hospital Management System - Login Verification',
    }
    
    context = {
        'otp_code': otp_code,
        'purpose': purpose,
        'expiry_minutes': 10 if purpose == 'verification' else 15,
        'hospital_name': 'Your Hospital Name',
        'support_email': 'support@yourhospital.com',
    }
    
    # Create HTML and plain text versions
    html_message = render_to_string(f'authentication/emails/{purpose}_otp.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject_templates.get(purpose, 'Hospital Management System - Verification'),
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False

def validate_patient_id_format(patient_id):
    """Validate patient ID format"""
    import re
    pattern = r'^HMS\d{4}\d{6}
          # HMS + year + 6 digits
    return bool(re.match(pattern, patient_id))

def validate_employee_id_format(employee_id):
    """Validate employee ID format"""
    import re
    pattern = r'^EMP\d{4}\d{4}
          # EMP + year + 4 digits
    return bool(re.match(pattern, employee_id))

def get_client_ip(request):
    """Get the real client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_audit_log(user, action, details, ip_address=None):
    """Create audit log entry"""
    from .models import AuditLog
    
    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            details=details,
            ip_address=ip_address or '127.0.0.1'
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create audit log: {str(e)}")

