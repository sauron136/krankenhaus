from rest_framework import serializers
from accounts.models import Personnel, Patient

class PersonnelLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)

class PatientLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class PersonnelRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Personnel
        fields = [
            'email', 'username', 'first_name', 'last_name', 
            'employee_id', 'phone_work', 'phone_personal', 
            'emergency_contact', 'date_of_birth', 'hire_date',
            'password', 'confirm_password'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        personnel = Personnel(**validated_data)
        personnel.set_password(password)
        personnel.is_active = False  # Will be activated after email verification
        personnel.save()
        return personnel

class PatientRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Patient
        fields = [
            'email', 'first_name', 'last_name', 'phone_primary',
            'phone_secondary', 'emergency_contact_name', 
            'emergency_contact_phone', 'date_of_birth', 'address',
            'password', 'confirm_password'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        patient = Patient(**validated_data)
        patient.set_password(password)
        patient.is_active = False  # Will be activated after email verification
        patient.save()
        return patient

class TokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class OTPVerificationSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_type = serializers.ChoiceField(choices=[('personnel', 'Personnel'), ('patient', 'Patient')])
    otp_code = serializers.CharField(max_length=6, min_length=6)

class ResendOTPSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_type = serializers.ChoiceField(choices=[('personnel', 'Personnel'), ('patient', 'Patient')])
    otp_type = serializers.ChoiceField(choices=[
        ('email_verification', 'Email Verification'),
        ('password_reset', 'Password Reset'),
        ('login_verification', 'Login Verification'),
        ('account_unlock', 'Account Unlock'),
    ])

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    user_type = serializers.ChoiceField(choices=[('personnel', 'Personnel'), ('patient', 'Patient')])

class PasswordResetConfirmSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_type = serializers.ChoiceField(choices=[('personnel', 'Personnel'), ('patient', 'Patient')])
    otp_code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
