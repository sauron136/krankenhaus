from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Personnel, Patient, Role, PersonnelRole

@admin.register(Personnel)
class PersonnelAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'employee_id', 'is_active', 'is_verified', 'hire_date')
    list_filter = ('is_active', 'is_verified', 'is_staff', 'hire_date')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'employee_id', 'date_of_birth')}),
        ('Contact Info', {'fields': ('phone_work', 'phone_personal', 'emergency_contact')}),
        ('Employment Info', {'fields': ('hire_date',)}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'created_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'employee_id', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('created_at',)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_primary', 'is_active', 'is_verified', 'date_registered')
    list_filter = ('is_active', 'is_verified', 'date_registered')
    search_fields = ('email', 'first_name', 'last_name', 'phone_primary')
    ordering = ('email',)
    
    fieldsets = (
        ('Account Info', {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'date_of_birth', 'address')}),
        ('Contact Info', {'fields': ('phone_primary', 'phone_secondary')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_phone')}),
        ('Status', {'fields': ('is_active', 'is_verified')}),
        ('Important Dates', {'fields': ('date_registered',)}),
    )
    
    readonly_fields = ('date_registered',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(PersonnelRole)
class PersonnelRoleAdmin(admin.ModelAdmin):
    list_display = ('personnel', 'role', 'assigned_date', 'expires_date', 'is_active', 'assigned_by')
    list_filter = ('is_active', 'assigned_date', 'expires_date')
    search_fields = ('personnel__username', 'personnel__first_name', 'personnel__last_name', 'role__name')
    ordering = ('-assigned_date',)
    
    fieldsets = (
        ('Assignment Info', {'fields': ('personnel', 'role')}),
        ('Assignment Details', {'fields': ('assigned_by', 'assigned_date', 'expires_date', 'is_active')}),
        ('Notes', {'fields': ('notes',)}),
    )
    
    readonly_fields = ('assigned_date',)
