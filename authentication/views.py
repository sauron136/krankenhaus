# authentication/views.py
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .jwt_handler import CustomJWTHandler, JWTTokenBlacklist
from django.contrib.auth import authenticate
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
import random
import string
from datetime import timedelta

from .models import User, OTPVerification
from .serializers import (
    UserRegistrationSerializer, 
    LoginSerializer, 
    OTPVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer
)
from accounts.models import Patient, Personnel

class PersonnelRegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Create user
            user = serializer.save()
            user.username = f"personnel_{user.id}"
            user.save()
            
            # Create personnel profile
            Personnel.objects.create_personnel_profile(user=user)
            
            # Generate and send OTP
            otp_code = self._generate_otp()
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                purpose='email_verification',
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            self._send_otp_email(user.email, otp_code, 'verification')
            
            return Response({
                'message': 'Personnel account created successfully. Please check your email for verification code.',
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
    
    def _generate_otp(self):
        return ''.join(random.choices(string.digits, k=6))
    
    def _send_otp_email(self, email, otp_code, purpose):
        subject_map = {
            'verification': 'Hospital Management System - Email Verification',
            'password_reset': 'Hospital Management System - Password Reset'
        }
        
        message = f"""
        Your verification code is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        send_mail(
            subject=subject_map.get(purpose, 'Hospital Management System - Verification'),
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )


class PatientRegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Create user
            user = serializer.save()
            user.username = user.email  # Patients use email as username
            user.save()
            
            # Create patient profile
            Patient.objects.create_patient_profile(
                user=user,
                registration_type='online'
            )
            
            # Generate and send OTP
            otp_code = self._generate_otp()
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                purpose='email_verification',
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            self._send_otp_email(user.email, otp_code, 'verification')
            
            return Response({
                'message': 'Patient account created successfully. Please check your email for verification code.',
                'user_id': user.id,
                'email': user.email,
                'patient_id': user.patient_profile.patient_id
            }, status=status.HTTP_201_CREATED)
    
    def _generate_otp(self):
        return ''.join(random.choices(string.digits, k=6))
    
    def _send_otp_email(self, email, otp_code, purpose):
        subject_map = {
            'verification': 'Hospital Management System - Email Verification',
            'password_reset': 'Hospital Management System - Password Reset'
        }
        
        message = f"""
        Your verification code is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        send_mail(
            subject=subject_map.get(purpose, 'Hospital Management System - Verification'),
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            user = User.objects.get(email=email)
            otp_verification = OTPVerification.objects.filter(
                user=user,
                otp_code=otp_code,
                purpose='email_verification',
                is_used=False
            ).first()
            
            if not otp_verification:
                return Response({
                    'error': 'Invalid OTP code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if otp_verification.is_expired():
                return Response({
                    'error': 'OTP code has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used and verify user
            otp_verification.is_used = True
            otp_verification.save()
            
            user.is_verified = True
            user.is_active = True
            user.save()
            
            # Generate JWT tokens
            tokens = CustomJWTHandler.generate_tokens(user)
            
            return Response({
                'message': 'Email verified successfully',
                **tokens,
                'user': tokens  # User data is already in the token payload
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


class PersonnelLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=email, password=password)
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_verified:
            return Response({
                'error': 'Please verify your email before logging in'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not hasattr(user, 'personnel_profile'):
            return Response({
                'error': 'Invalid account type for personnel login'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Update last login
        user.last_login = timezone.now()
        user.save()
        
        # Generate JWT tokens
        tokens = CustomJWTHandler.generate_tokens(user)
        
        return Response({
            'message': 'Login successful',
            **tokens
        }, status=status.HTTP_200_OK)
    
    def _get_user_permissions(self, personnel):
        """Get user permissions based on their roles"""
        roles = personnel.role_assignments.filter(is_active=True).select_related('role')
        permissions = set()
        
        for role_assignment in roles:
            role = role_assignment.role
            if role.access_level == 'basic':
                permissions.update(['view_patient_basic_info'])
            elif role.access_level == 'medical':
                permissions.update([
                    'view_patient_basic_info',
                    'view_patient_medical_records',
                    'create_medical_records',
                    'view_prescriptions',
                    'view_lab_results'
                ])
            elif role.access_level == 'senior_medical':
                permissions.update([
                    'view_patient_basic_info',
                    'view_patient_medical_records',
                    'create_medical_records',
                    'edit_medical_records',
                    'view_prescriptions',
                    'create_prescriptions',
                    'view_lab_results',
                    'order_lab_tests',
                    'emergency_override'
                ])
            elif role.access_level == 'administrative':
                permissions.update([
                    'view_patient_basic_info',
                    'manage_appointments',
                    'manage_inventory',
                    'view_reports',
                    'manage_personnel'
                ])
            elif role.access_level == 'emergency':
                permissions.update([
                    'view_patient_basic_info',
                    'view_patient_medical_records',
                    'create_medical_records',
                    'emergency_override',
                    'critical_access'
                ])
        
        return list(permissions)


class PatientLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=email, password=password)
        
        if not user:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_verified:
            return Response({
                'error': 'Please verify your email before logging in'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not hasattr(user, 'patient_profile'):
            return Response({
                'error': 'Invalid account type for patient login'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Update last login
        user.last_login = timezone.now()
        user.save()
        
        # Generate JWT tokens
        tokens = CustomJWTHandler.generate_tokens(user)
        
        return Response({
            'message': 'Login successful',
            **tokens
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                JWTTokenBlacklist.blacklist_token(refresh_token)
            
            # Also try to blacklist access token if provided
            access_token = request.data.get('access_token')
            if access_token:
                JWTTokenBlacklist.blacklist_token(access_token)
            
            return Response({
                'message': 'Logged out successfully'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is already verified
            if user.is_verified:
                return Response({
                    'error': 'Email is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Invalidate previous OTPs
            OTPVerification.objects.filter(
                user=user,
                purpose='email_verification',
                is_used=False
            ).update(is_used=True)
            
            # Generate new OTP
            otp_code = ''.join(random.choices(string.digits, k=6))
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                purpose='email_verification',
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            
            # Send OTP email
            self._send_otp_email(user.email, otp_code, 'verification')
            
            return Response({
                'message': 'New verification code sent successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def _send_otp_email(self, email, otp_code, purpose):
        subject_map = {
            'verification': 'Hospital Management System - Email Verification',
            'password_reset': 'Hospital Management System - Password Reset'
        }
        
        message = f"""
        Your verification code is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        send_mail(
            subject=subject_map.get(purpose, 'Hospital Management System - Verification'),
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Invalidate previous password reset OTPs
            OTPVerification.objects.filter(
                user=user,
                purpose='password_reset',
                is_used=False
            ).update(is_used=True)
            
            # Generate new OTP
            otp_code = ''.join(random.choices(string.digits, k=6))
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                purpose='password_reset',
                expires_at=timezone.now() + timedelta(minutes=15)
            )
            
            # Send OTP email
            self._send_otp_email(user.email, otp_code, 'password_reset')
            
            return Response({
                'message': 'Password reset code sent successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Don't reveal whether user exists or not
            return Response({
                'message': 'Password reset code sent successfully'
            }, status=status.HTTP_200_OK)
    
    def _send_otp_email(self, email, otp_code, purpose):
        subject_map = {
            'verification': 'Hospital Management System - Email Verification',
            'password_reset': 'Hospital Management System - Password Reset'
        }
        
        message = f"""
        Your password reset code is: {otp_code}
        
        This code will expire in 15 minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        send_mail(
            subject=subject_map.get(purpose, 'Hospital Management System - Password Reset'),
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(email=email)
            otp_verification = OTPVerification.objects.filter(
                user=user,
                otp_code=otp_code,
                purpose='password_reset',
                is_used=False
            ).first()
            
            if not otp_verification:
                return Response({
                    'error': 'Invalid OTP code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if otp_verification.is_expired():
                return Response({
                    'error': 'OTP code has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark OTP as used and reset password
            otp_verification.is_used = True
            otp_verification.save()
            
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password reset successfully'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        user = request.user
        
        if not user.check_password(old_password):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Check if token is blacklisted
            if JWTTokenBlacklist.is_token_blacklisted(refresh_token):
                return Response({
                    'error': 'Token has been revoked'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate new access token
            tokens = CustomJWTHandler.refresh_access_token(refresh_token)
            
            return Response({
                'message': 'Token refreshed successfully',
                **tokens
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


class ValidateTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # User data is already in the token payload via our custom authentication
        token_payload = getattr(request.user, 'token_payload', {})
        
        return Response({
            'valid': True,
            'user': {
                'id': token_payload.get('user_id'),
                'email': token_payload.get('email'),
                'first_name': token_payload.get('first_name'),
                'last_name': token_payload.get('last_name'),
                'user_type': token_payload.get('user_type'),
                'permissions': token_payload.get('permissions', []),
                # Patient-specific data
                'patient_id': token_payload.get('patient_id'),
                'is_profile_complete': token_payload.get('is_profile_complete'),
                # Personnel-specific data
                'employee_id': token_payload.get('employee_id'),
                'is_verified': token_payload.get('is_verified'),
                'verification_status': token_payload.get('verification_status'),
                'roles': token_payload.get('roles', []),
                'can_trigger_emergency': token_payload.get('can_trigger_emergency', False)
            }
        }, status=status.HTTP_200_OK)
    
    def _get_user_permissions(self, personnel):
        """Get user permissions based on their roles - same as in PersonnelLoginView"""
        roles = personnel.role_assignments.filter(is_active=True).select_related('role')
        permissions = set()
        
        for role_assignment in roles:
            role = role_assignment.role
            if role.access_level == 'basic':
                permissions.update(['view_patient_basic_info'])
            elif role.access_level == 'medical':
                permissions.update([
                    'view_patient_basic_info',
                    'view_patient_medical_records',
                    'create_medical_records',
                    'view_prescriptions',
                    'view_lab_results'
                ])
            elif role.access_level == 'senior_medical':
                permissions.update([
                    'view_patient_basic_info',
                    'view_patient_medical_records',
                    'create_medical_records',
                    'edit_medical_records',
                    'view_prescriptions',
                    'create_prescriptions',
                    'view_lab_results',
                    'order_lab_tests',
                    'emergency_override'
                ])
            elif role.access_level == 'administrative':
                permissions.update([
                    'view_patient_basic_info',
                    'manage_appointments',
                    'manage_inventory',
                    'view_reports',
                    'manage_personnel'
                ])
            elif role.access_level == 'emergency':
                permissions.update([
                    'view_patient_basic_info',
                    'view_patient_medical_records',
                    'create_medical_records',
                    'emergency_override',
                    'critical_access'
                ])
        
        return list(permissions)
