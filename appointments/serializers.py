from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, time
from .models import (
    Department, 
    AppointmentType, 
    ProviderAvailability, 
    Appointment, 
    AppointmentStatusHistory
)
from accounts.models import Personnel, Patient

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class AppointmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentType
        fields = ['id', 'name', 'description', 'duration_minutes', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProviderAvailabilitySerializer(serializers.ModelSerializer):
    provider_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProviderAvailability
        fields = [
            'id', 'provider', 'provider_name', 'day_of_week', 
            'start_time', 'end_time', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_provider_name(self, obj):
        return f"{obj.provider.first_name} {obj.provider.last_name}"

class ProviderAvailabilityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAvailability
        fields = ['provider', 'day_of_week', 'start_time', 'end_time']
    
    def validate(self, attrs):
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError("Start time must be before end time")
        return attrs

class PatientBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_primary']

class ProviderBasicSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = Personnel
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'employee_id', 'roles']
    
    def get_roles(self, obj):
        return list(obj.role_assignments.filter(is_active=True).values_list('role__name', flat=True))

class AppointmentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    appointment_type_name = serializers.CharField(source='appointment_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient_name', 'provider_name', 'department_name', 
            'appointment_type_name', 'appointment_date', 'appointment_time',
            'duration_minutes', 'status', 'status_display', 'priority', 
            'priority_display', 'reason_for_visit', 'created_at'
        ]
    
    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    
    def get_provider_name(self, obj):
        return f"{obj.provider.first_name} {obj.provider.last_name}"

class AppointmentDetailSerializer(serializers.ModelSerializer):
    patient = PatientBasicSerializer(read_only=True)
    provider = ProviderBasicSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    appointment_type = AppointmentTypeSerializer(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    end_time = serializers.TimeField(read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'provider', 'department', 'appointment_type',
            'appointment_date', 'appointment_time', 'end_time', 'duration_minutes',
            'status', 'status_display', 'priority', 'priority_display',
            'reason_for_visit', 'notes', 'special_instructions',
            'is_follow_up', 'parent_appointment', 'created_by_name',
            'created_at', 'updated_at'
        ]
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None

class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'patient', 'provider', 'department', 'appointment_type',
            'appointment_date', 'appointment_time', 'reason_for_visit',
            'priority', 'notes', 'special_instructions', 'is_follow_up',
            'parent_appointment'
        ]
    
    def validate_appointment_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Appointment date cannot be in the past")
        return value
    
    def validate_appointment_time(self, value):
        # Basic validation - ensure it's during business hours (8 AM - 6 PM)
        if value < time(8, 0) or value > time(18, 0):
            raise serializers.ValidationError("Appointments must be scheduled between 8:00 AM and 6:00 PM")
        return value
    
    def validate(self, attrs):
        appointment_datetime = datetime.combine(attrs['appointment_date'], attrs['appointment_time'])
        if appointment_datetime <= timezone.now():
            raise serializers.ValidationError("Appointment must be scheduled for a future date/time")
        
        # Check for provider availability on that day/time
        day_of_week = attrs['appointment_date'].strftime('%A').lower()
        provider_available = ProviderAvailability.objects.filter(
            provider=attrs['provider'],
            day_of_week=day_of_week,
            start_time__lte=attrs['appointment_time'],
            end_time__gt=attrs['appointment_time'],
            is_active=True
        ).exists()
        
        if not provider_available:
            raise serializers.ValidationError("Provider is not available at the requested time")
        
        # Check for conflicting appointments
        duration = attrs.get('duration_minutes') or attrs['appointment_type'].duration_minutes
        end_time = (appointment_datetime + timezone.timedelta(minutes=duration)).time()
        
        conflicting_appointments = Appointment.objects.filter(
            provider=attrs['provider'],
            appointment_date=attrs['appointment_date'],
            status__in=['scheduled', 'confirmed', 'checked_in', 'in_progress']
        ).exclude(id=getattr(self.instance, 'id', None))
        
        for apt in conflicting_appointments:
            if (attrs['appointment_time'] < apt.end_time and end_time > apt.appointment_time):
                raise serializers.ValidationError(
                    f"Provider has a conflicting appointment from {apt.appointment_time} to {apt.end_time}"
                )
        
        return attrs
    
    def create(self, validated_data):
        # Set duration from appointment type if not provided
        if 'duration_minutes' not in validated_data:
            validated_data['duration_minutes'] = validated_data['appointment_type'].duration_minutes
        
        return super().create(validated_data)

class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'appointment_date', 'appointment_time', 'status', 'priority',
            'notes', 'special_instructions', 'reason_for_visit'
        ]
    
    def validate_status(self, value):
        if self.instance and self.instance.status == 'completed' and value != 'completed':
            raise serializers.ValidationError("Cannot change status of completed appointment")
        return value

class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    reason = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Appointment
        fields = ['status', 'reason']
    
    def validate_status(self, value):
        valid_transitions = {
            'scheduled': ['confirmed', 'cancelled', 'rescheduled'],
            'confirmed': ['checked_in', 'cancelled', 'no_show'],
            'checked_in': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],  # Cannot change from completed
            'cancelled': ['scheduled'],  # Can reschedule cancelled appointments
            'no_show': ['scheduled'],  # Can reschedule no-shows
            'rescheduled': ['scheduled'],
        }
        
        current_status = self.instance.status if self.instance else 'scheduled'
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}'"
            )
        return value

class AppointmentSearchSerializer(serializers.Serializer):
    patient_name = serializers.CharField(required=False, allow_blank=True)
    provider_id = serializers.IntegerField(required=False)
    department_id = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    appointment_type_id = serializers.IntegerField(required=False)
    priority = serializers.CharField(required=False, allow_blank=True)

class AppointmentStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()
    old_status_display = serializers.SerializerMethodField()
    new_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AppointmentStatusHistory
        fields = [
            'id', 'old_status', 'old_status_display', 'new_status', 
            'new_status_display', 'changed_by_name', 'reason', 'changed_at'
        ]
    
    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return f"{obj.changed_by.first_name} {obj.changed_by.last_name}"
        return "System"
    
    def get_old_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.old_status, obj.old_status)
    
    def get_new_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.new_status, obj.new_status)
