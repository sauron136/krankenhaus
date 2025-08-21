# authentication/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'confirm_password')
    
    def validate_email(self, value):
        """Validate email format and uniqueness"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Please enter a valid email address.")
        
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        return value.lower()
    
    def validate_first_name(self, value):
        """Validate first name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long.")
        
        if not re.match(r'^[a-zA-Z\s\'-]+$', value):
            raise serializers.ValidationError("First name can only contain letters, spaces, apostrophes, and hyphens.")
        
        return value.title().strip()
    
    def validate_last_name(self, value):
        """Validate last name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long.")
        
        if not re.match(r'^[a-zA-Z\s\'-]+$', value):
            raise serializers.ValidationError("Last name can only contain letters, spaces, apostrophes, and hyphens.")
        
        return value.title().strip()
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create user account"""
        validated_data.pop('confirm_password')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower().strip()
    
    def validate(self, attrs):
        """Validate login credentials format"""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email:
            raise serializers.ValidationError({
                'email': 'Email is required.'
            })
        
        if not password:
            raise serializers.ValidationError({
                'password': 'Password is required.'
            })
        
        return attrs


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower().strip()
    
    def validate_otp_code(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only numbers.")
        
        if len(value) != 6:
            raise serializers.ValidationError("OTP code must be exactly 6 digits.")
        
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_email(self, value):
        """Normalize email"""
        return value.lower().strip()
    
    def validate_otp_code(self, value):
        """Validate OTP format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only numbers.")
        
        if len(value) != 6:
            raise serializers.ValidationError("OTP code must be exactly 6 digits.")
        
        return value
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match."
            })
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return value
    
    def validate(self, attrs):
        """Validate that passwords match and old password is different from new"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match."
            })
        
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': "New password must be different from the current password."
            })
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for basic user profile information"""
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_active', 'is_verified', 'created_at')
        read_only_fields = ('id', 'email', 'is_active', 'is_verified', 'created_at')
    
    def validate_first_name(self, value):
        """Validate first name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters long.")
        
        if not re.match(r'^[a-zA-Z\s\'-]+$', value):
            raise serializers.ValidationError("First name can only contain letters, spaces, apostrophes, and hyphens.")
        
        return value.title().strip()
    
    def validate_last_name(self, value):
        """Validate last name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters long.")
        
        if not re.match(r'^[a-zA-Z\s\'-]+$', value):
            raise serializers.ValidationError("Last name can only contain letters, spaces, apostrophes, and hyphens.")
        
        return value.title().strip()


class TokenValidationSerializer(serializers.Serializer):
    """Serializer for token validation responses"""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField(required=False)
    expires_in = serializers.IntegerField()
    token_type = serializers.CharField()


# Custom validation mixins
class EmailValidationMixin:
    """Mixin for common email validation"""
    
    def validate_email_format(self, email):
        """Validate email format"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email):
            raise serializers.ValidationError("Please enter a valid email address.")
        return email.lower().strip()


class PasswordValidationMixin:
    """Mixin for common password validation"""
    
    def validate_password_strength(self, password):
        """Validate password meets security requirements"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter.")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number.")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character.")
        
        # Check against common passwords
        common_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 
            'password123', 'admin', 'letmein', 'welcome'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common. Please choose a more secure password.")
        
        if errors:
            raise serializers.ValidationError(errors)
        
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        
        return password


class NameValidationMixin:
    """Mixin for name field validation"""
    
    def validate_name_field(self, value, field_name):
        """Validate name fields (first_name, last_name)"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(f"{field_name} must be at least 2 characters long.")
        
        if not re.match(r'^[a-zA-Z\s\'-]+$', value):
            raise serializers.ValidationError(f"{field_name} can only contain letters, spaces, apostrophes, and hyphens.")
        
        # Check for excessive whitespace or repeated characters
        if '  ' in value or len(set(value.replace(' ', '').replace("'", '').replace('-', ''))) < 2:
            raise serializers.ValidationError(f"Please enter a valid {field_name.lower()}.")
        
        return value.title().strip()
