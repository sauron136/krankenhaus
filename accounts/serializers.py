from rest_framework import serializers
from .models import Personnel, Patient, Role, PersonnelRole

class PersonnelProfileSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Personnel
        fields = [
                'id', 'email', 'username', 'first_name', 'last_name',
                'employee_id', 'phone_work', 'phone_personal',
                'emergency_contact', 'date_of_birth', 'hire_date',
                'is_active', 'is_verified', 'created_at', 'role'
                ]
        read_only_fields = ['id', 'created_at', 'is_verified']

    def get_roles(self, obj):
        active_roles = obj.role_assignments.filter(is_active=True)
        return RoleAssignmentSerializer(active_roles, many=True).data

class PersonnelUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Personnel
        fields = [
                'first_name', 'last_name', 'phone_work', 'phone_personal',
                'emergency_contact'
                ]

class PersonnelListSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = Personnel
        fields = [
                'id', 'username', 'first_name', 'last_name', 'email',
                'employee_id', 'is_active', 'hire_date', 'roles'
                ]

    def get_roles(self, obj):
        active_roles = obj.role_assignments.filter(is_active=True).values_list('role__name', flat=True)
        return list(active_roles)

class PersonnelSearchSerializer(serializers.Serializer):
    query = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    hire_date_from = serializers.DateField(required=False)
    hire_date_to = serializers.DateField(required=False)

class PersonnelCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Personnel
        fields = [
                'email', 'username', 'first_name', 'last_name',
                'employee_id', 'phone_work', 'phone_personal',
                'emergency_contact', 'date_of_birth', 'hire_date',
                'password'
                ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        personnel = Personnel(**validated_data)
        personnel.set_password(password)
        personnel.is_active = True
        personnel.is_verified = True
        personnel.save()
        return personnel

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
                'id', 'email', 'first_name', 'last_name', 'phone_primary',
                'phone_secondary', 'emergency_contact_name', 
                'emergency_contact_phone', 'date_of_birth', 'address',
                'is_active', 'is_verified', 'date_registered'
                ]
        read_only_fields = ['id', 'date_registered', 'is_verified']

class PatientUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
                'first_name', 'last_name', 'phone_primary', 'phone_secondary',
                'emergency_contact_name', 'emergency_contact_phone', 'address'
                ]

class PatientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = [
                'id', 'email', 'first_name', 'last_name', 'phone_primary',
                'date_of_birth', 'is_active', 'date_registered'
                ]

class RoleSerializer(serializers.ModelSerializer):
    personnel_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'created_at', 'personnel_count']
        read_only_fields = ['id', 'created_at']
    
    def get_personnel_count(self, obj):
        return obj.personnelrole_set.filter(is_active=True).count()

class RoleAssignmentSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PersonnelRole
        fields = [
            'id', 'role_name', 'assigned_date', 'expires_date',
            'is_active', 'notes', 'assigned_by_name'
        ]
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return f"{obj.assigned_by.first_name} {obj.assigned_by.last_name}"
        return None

class AssignRoleSerializer(serializers.Serializer):
    personnel_id = serializers.IntegerField()
    role_id = serializers.IntegerField()
    expires_date = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
