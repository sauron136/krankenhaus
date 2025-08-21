from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Patient, Personnel, Role, EmergencyAccess

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for profiles"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class RoleSerializer(serializers.ModelSerializer):
    """Role serializer"""
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'can_emergency_override']


class PatientProfileSerializer(serializers.ModelSerializer):
    """Full patient profile for viewing"""
    user = UserBasicSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = Patient
        fields = [
            'patient_id', 'user', 'full_name', 'phone_number', 
            'date_of_birth', 'age', 'gender', 'address', 
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'blood_group',
            'allergies', 'medical_conditions', 'current_medications',
            'insurance_provider', 'insurance_policy_number',
            'profile_completed', 'created_at', 'updated_at'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def get_age(self, obj):
        if obj.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - obj.date_of_birth.year
            if today.month < obj.date_of_birth.month or \
               (today.month == obj.date_of_birth.month and today.day < obj.date_of_birth.day):
                age -= 1
            return age
        return None


class PatientUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating patient profile"""
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth', 
            'gender', 'address', 'emergency_contact_name', 
            'emergency_contact_phone', 'emergency_contact_relationship',
            'blood_group', 'allergies', 'medical_conditions', 
            'current_medications', 'insurance_provider', 'insurance_policy_number'
        ]
    
    def validate_phone_number(self, value):
        if value and len(value.replace(' ', '').replace('-', '').replace('+', '')) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_emergency_contact_phone(self, value):
        if value and len(value.replace(' ', '').replace('-', '').replace('+', '')) < 10:
            raise serializers.ValidationError("Emergency contact phone must be at least 10 digits")
        return value
    
    def update(self, instance, validated_data):
        # Handle nested user data
        user_data = validated_data.pop('user', {})
        
        # Update user fields
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()
        
        # Update patient fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class PersonnelProfileSerializer(serializers.ModelSerializer):
    """Full personnel profile for viewing"""
    user = UserBasicSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Personnel
        fields = [
            'employee_id', 'user', 'full_name', 'role', 'department',
            'phone_number', 'date_of_birth', 'address', 'hire_date',
            'medical_license_number', 'specialization', 'is_verified',
            'created_at', 'updated_at'
        ]
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class PersonnelUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating personnel profile"""
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = Personnel
        fields = [
            'first_name', 'last_name', 'department', 'phone_number',
            'date_of_birth', 'address', 'medical_license_number', 'specialization'
        ]
    
    def validate_phone_number(self, value):
        if value and len(value.replace(' ', '').replace('-', '').replace('+', '')) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value
    
    def validate_medical_license_number(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Medical license number must be at least 5 characters")
        return value
    
    def update(self, instance, validated_data):
        # Handle nested user data
        user_data = validated_data.pop('user', {})
        
        # Update user fields
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()
        
        # Update personnel fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class PersonnelVerificationSerializer(serializers.Serializer):
    """Serializer for personnel verification by admin"""
    employee_id = serializers.CharField(max_length=20)
    action = serializers.ChoiceField(choices=['verify', 'reject'])
    role_id = serializers.IntegerField(required=False)
    
    def validate_action(self, value):
        if value not in ['verify', 'reject']:
            raise serializers.ValidationError("Action must be 'verify' or 'reject'")
        return value
    
    def validate(self, attrs):
        if attrs.get('action') == 'verify' and not attrs.get('role_id'):
            raise serializers.ValidationError("Role is required when verifying personnel")
        return attrs


class EmergencyAccessSerializer(serializers.ModelSerializer):
    """Serializer for emergency access logs"""
    patient_name = serializers.SerializerMethodField()
    personnel_name = serializers.SerializerMethodField()
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    employee_id = serializers.CharField(source='personnel.employee_id', read_only=True)
    
    class Meta:
        model = EmergencyAccess
        fields = [
            'id', 'patient_id', 'patient_name', 'employee_id', 
            'personnel_name', 'reason', 'search_method', 
            'ip_address', 'accessed_at'
        ]
    
    def get_patient_name(self, obj):
        return f"{obj.patient.user.first_name} {obj.patient.user.last_name}".strip()
    
    def get_personnel_name(self, obj):
        return f"{obj.personnel.user.first_name} {obj.personnel.user.last_name}".strip()


class PatientSearchSerializer(serializers.Serializer):
    """Serializer for patient search"""
    query = serializers.CharField(max_length=255, required=False)
    patient_id = serializers.CharField(max_length=20, required=False)
    
    def validate(self, attrs):
        if not attrs.get('query') and not attrs.get('patient_id'):
            raise serializers.ValidationError("Either query or patient_id is required")
        
        if attrs.get('query') and len(attrs['query']) < 2:
            raise serializers.ValidationError("Query must be at least 2 characters long")
        
        return attrs


class PersonnelSearchSerializer(serializers.Serializer):
    """Serializer for personnel search"""
    query = serializers.CharField(max_length=255)
    role = serializers.CharField(max_length=50, required=False)
    
    def validate_query(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Query must be at least 2 characters long")
        return value
