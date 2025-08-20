from django.db import models

class CustomJWTToken(models.Model):
    TOKEN_TYPES = (
        ('access', 'Access Token'),
        ('refresh', 'Refresh Token'),
    )
    
    personnel = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, null=True, blank=True, related_name='auth_tokens')
    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, null=True, blank=True, related_name='auth_tokens')
    token = models.TextField()
    token_type = models.CharField(max_length=10, choices=TOKEN_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'custom_jwt_tokens'
    
    @property 
    def user(self):
        return self.personnel or self.patient

class OTPToken(models.Model):
    OTP_TYPES = (
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('login_verification', 'Login Verification'),
        ('account_unlock', 'Account Unlock'),
    )
    
    personnel = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, null=True, blank=True, related_name='otp_tokens')
    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, null=True, blank=True, related_name='otp_tokens')
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    @property
    def user(self):
        return self.personnel or self.patient

class AccountLock(models.Model):
    LOCK_REASONS = (
        ('failed_attempts', 'Failed Login Attempts'),
        ('security_breach', 'Security Breach'),
        ('admin_action', 'Admin Action'),
        ('suspicious_activity', 'Suspicious Activity'),
    )
    
    personnel = models.OneToOneField('accounts.Personnel', on_delete=models.CASCADE, null=True, blank=True, related_name='account_lock')
    patient = models.OneToOneField('accounts.Patient', on_delete=models.CASCADE, null=True, blank=True, related_name='account_lock')
    locked_at = models.DateTimeField(auto_now_add=True)
    unlock_at = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=20, choices=LOCK_REASONS)
    locked_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True, related_name='accounts_locked')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    @property
    def user(self):
        return self.personnel or self.patient
