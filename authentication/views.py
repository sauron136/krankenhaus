from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from accounts.models import Personnel, Patient
from .services.jwt_service import JWTService
from .services.otp_service import OTPService
from .serializers import (
    PersonnelLoginSerializer, 
    PatientLoginSerializer,
    PersonnelRegisterSerializer,
    PatientRegisterSerializer,
    TokenRefreshSerializer,
    OTPVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ResendOTPSerializer,
    ChangePasswordSerializer
)

class PersonnelLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PersonnelLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            try:
                personnel = Personnel.objects.get(username=username)
                if personnel.check_password(password):
                    if not personnel.is_active:
                        return Response({
                            'error': 'Account is not activated. Please verify your email.'
                        }, status=status.HTTP_401_UNAUTHORIZED)
                    
                    tokens = JWTService.generate_token_pair(personnel, request)
                    return Response({
                        'message': 'Login successful',
                        'user_type': 'personnel',
                        'user': {
                            'id': personnel.id,
                            'username': personnel.username,
                            'email': personnel.email,
                            'first_name': personnel.first_name,
                            'last_name': personnel.last_name
                        },
                        'tokens': tokens
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Invalid credentials'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            except Personnel.DoesNotExist:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PatientLoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            try:
                patient = Patient.objects.get(email=email)
                if patient.check_password(password):
                    if not patient.is_active:
                        return Response({
                            'error': 'Account is not activated. Please verify your email.'
                        }, status=status.HTTP_401_UNAUTHORIZED)
                    
                    tokens = JWTService.generate_token_pair(patient, request)
                    return Response({
                        'message': 'Login successful',
                        'user_type': 'patient',
                        'user': {
                            'id': patient.id,
                            'email': patient.email,
                            'first_name': patient.first_name,
                            'last_name': patient.last_name
                        },
                        'tokens': tokens
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Invalid credentials'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            except Patient.DoesNotExist:
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PersonnelRegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PersonnelRegisterSerializer(data=request.data)
        if serializer.is_valid():
            personnel = serializer.save()
            
            # Send email verification OTP
            otp_token = OTPService.create_otp(personnel, 'email_verification', request)
            OTPService.send_otp_email(personnel, otp_token.otp_code, 'email_verification')
            
            return Response({
                'message': 'Personnel registered successfully. Please check your email for verification code.',
                'user_id': personnel.id,
                'email': personnel.email
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientRegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PatientRegisterSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            
            # Send email verification OTP
            otp_token = OTPService.create_otp(patient, 'email_verification', request)
            OTPService.send_otp_email(patient, otp_token.otp_code, 'email_verification')
            
            return Response({
                'message': 'Patient registered successfully. Please check your email for verification code.',
                'user_id': patient.id,
                'email': patient.email
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            user_type = serializer.validated_data['user_type']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                if user_type == 'personnel':
                    user = Personnel.objects.get(id=user_id)
                else:
                    user = Patient.objects.get(id=user_id)
                
                if OTPService.verify_otp(user, otp_code, 'email_verification'):
                    # Mark user as verified and active
                    user.is_active = True
                    user.is_verified = True
                    user.save()
                    
                    # Generate tokens for automatic login
                    tokens = JWTService.generate_token_pair(user, request)
                    
                    return Response({
                        'message': 'Email verified successfully',
                        'tokens': tokens
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Invalid or expired OTP code'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except (Personnel.DoesNotExist, Patient.DoesNotExist):
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            user_type = serializer.validated_data['user_type']
            otp_type = serializer.validated_data['otp_type']
            
            try:
                if user_type == 'personnel':
                    user = Personnel.objects.get(id=user_id)
                else:
                    user = Patient.objects.get(id=user_id)
                
                # Create new OTP
                otp_token = OTPService.create_otp(user, otp_type, request)
                OTPService.send_otp_email(user, otp_token.otp_code, otp_type)
                
                return Response({
                    'message': 'OTP sent successfully'
                }, status=status.HTTP_200_OK)
                
            except (Personnel.DoesNotExist, Patient.DoesNotExist):
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user_type = serializer.validated_data['user_type']
            
            try:
                if user_type == 'personnel':
                    user = Personnel.objects.get(email=email)
                else:
                    user = Patient.objects.get(email=email)
                
                # Create password reset OTP
                otp_token = OTPService.create_otp(user, 'password_reset', request)
                OTPService.send_otp_email(user, otp_token.otp_code, 'password_reset')
                
                return Response({
                    'message': 'Password reset code sent to your email',
                    'user_id': user.id
                }, status=status.HTTP_200_OK)
                
            except (Personnel.DoesNotExist, Patient.DoesNotExist):
                return Response({
                    'error': 'User with this email does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            user_type = serializer.validated_data['user_type']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']
            
            try:
                if user_type == 'personnel':
                    user = Personnel.objects.get(id=user_id)
                else:
                    user = Patient.objects.get(id=user_id)
                
                if OTPService.verify_otp(user, otp_code, 'password_reset'):
                    # Update password
                    user.set_password(new_password)
                    user.save()
                    
                    return Response({
                        'message': 'Password reset successfully'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Invalid or expired OTP code'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except (Personnel.DoesNotExist, Patient.DoesNotExist):
                return Response({
                    'error': 'User not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = []  # Add authentication permission here
    
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            current_password = serializer.validated_data['current_password']
            new_password = serializer.validated_data['new_password']
            
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                
                return Response({
                    'message': 'Password changed successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Current password is incorrect'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            refresh_token = serializer.validated_data['refresh_token']
            
            try:
                tokens = JWTService.refresh_access_token(refresh_token, request)
                return Response({
                    'message': 'Token refreshed successfully',
                    'tokens': tokens
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ValidateTokenView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            try:
                payload, token_obj = JWTService.validate_token(token)
                user = token_obj.user
                
                return Response({
                    'valid': True,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'user_type': 'personnel' if hasattr(user, 'username') else 'patient'
                    }
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'valid': False,
                    'error': str(e)
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'valid': False,
            'error': 'Token not provided'
        }, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            try:
                JWTService.revoke_token(token)
                return Response({
                    'message': 'Logged out successfully'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'error': 'Invalid token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'error': 'Token not provided'
        }, status=status.HTTP_400_BAD_REQUEST)
