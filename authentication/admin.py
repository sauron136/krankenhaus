from django.contrib import admin
from .models import CustomJWTToken, OTPToken, AccountLock

@admin.register(CustomJWTToken)
class CustomJWTTokenAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'token_type', 'created_at', 'expires_at', 'last_used', 'is_active')
    list_filter = ('token_type', 'is_active', 'created_at', 'expires_at')
    search_fields = ('personnel__username', 'patient__email', 'ip_address')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Info', {'fields': ('personnel', 'patient')}),
        ('Token Info', {'fields': ('token_type', 'expires_at', 'is_active')}),
        ('Usage Info', {'fields': ('created_at', 'last_used', 'ip_address', 'user_agent')}),
        ('Token Data', {'fields': ('token',)}),
    )
    
    readonly_fields = ('created_at', 'token')
    
    def get_user(self, obj):
        return obj.user
    get_user.short_description = 'User'

@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'otp_type', 'otp_code', 'created_at', 'expires_at', 'is_used', 'attempts')
    list_filter = ('otp_type', 'is_used', 'created_at', 'expires_at')
    search_fields = ('personnel__username', 'patient__email', 'otp_code', 'ip_address')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Info', {'fields': ('personnel', 'patient')}),
        ('OTP Info', {'fields': ('otp_code', 'otp_type', 'expires_at', 'is_used', 'attempts')}),
        ('Request Info', {'fields': ('created_at', 'ip_address')}),
    )
    
    readonly_fields = ('created_at',)
    
    def get_user(self, obj):
        return obj.user
    get_user.short_description = 'User'

@admin.register(AccountLock)
class AccountLockAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'reason', 'locked_at', 'unlock_at', 'locked_by', 'is_active')
    list_filter = ('reason', 'is_active', 'locked_at')
    search_fields = ('personnel__username', 'patient__email', 'locked_by__username')
    ordering = ('-locked_at',)
    
    fieldsets = (
        ('Locked User', {'fields': ('personnel', 'patient')}),
        ('Lock Details', {'fields': ('reason', 'locked_by', 'locked_at', 'unlock_at', 'is_active')}),
        ('Notes', {'fields': ('notes',)}),
    )
    
    readonly_fields = ('locked_at',)
    
    def get_user(self, obj):
        return obj.user
    get_user.short_description = 'Locked User'
