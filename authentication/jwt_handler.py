import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

User = get_user_model()

class CustomJWTHandler:
    @staticmethod
    def generate_tokens(user):
        """Generate access and refresh tokens for a user"""
        
        # Get user type and profile data
        user_data = CustomJWTHandler._get_user_data(user)
        
        # Access token payload (expires in 1 hour)
        access_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user_data['user_type'],
            'permissions': user_data['permissions'],
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        # Add type-specific data to access token
        if user_data['user_type'] == 'patient':
            access_payload.update({
                'patient_id': user_data['patient_id'],
                'is_profile_complete': user_data['is_profile_complete']
            })
        elif user_data['user_type'] == 'personnel':
            access_payload.update({
                'employee_id': user_data['employee_id'],
                'is_verified': user_data['is_verified'],
                'verification_status': user_data['verification_status'],
                'roles': user_data['roles'],
                'can_trigger_emergency': user_data['can_trigger_emergency']
            })
        
        # Refresh token payload (expires in 7 days)
        refresh_payload = {
            'user_id': str(user.id),
            'email': user.email,
            'user_type': user_data['user_type'],
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        # Generate tokens
        access_token = jwt.encode(
            access_payload, 
            settings.SECRET_KEY, 
            algorithm='HS256'
        )
        
        refresh_token = jwt.encode(
            refresh_payload, 
            settings.SECRET_KEY, 
            algorithm='HS256'
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 3600,  # 1 hour in seconds
            'token_type': 'Bearer'
        }
    
    @staticmethod
    def decode_token(token):
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """Generate new access token from refresh token"""
        try:
            payload = CustomJWTHandler.decode_token(refresh_token)
            
            if payload.get('type') != 'refresh':
                raise AuthenticationFailed('Invalid token type')
            
            # Get user from payload
            user_id = payload.get('user_id')
            user = User.objects.get(id=user_id, is_active=True)
            
            # Generate new access token only
            user_data = CustomJWTHandler._get_user_data(user)
            
            access_payload = {
                'user_id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user_data['user_type'],
                'permissions': user_data['permissions'],
                'exp': datetime.utcnow() + timedelta(hours=1),
                'iat': datetime.utcnow(),
                'type': 'access'
            }
            
            # Add type-specific data
            if user_data['user_type'] == 'patient':
                access_payload.update({
                    'patient_id': user_data['patient_id'],
                    'is_profile_complete': user_data['is_profile_complete']
                })
            elif user_data['user_type'] == 'personnel':
                access_payload.update({
                    'employee_id': user_data['employee_id'],
                    'is_verified': user_data['is_verified'],
                    'verification_status': user_data['verification_status'],
                    'roles': user_data['roles'],
                    'can_trigger_emergency': user_data['can_trigger_emergency']
                })
            
            access_token = jwt.encode(
                access_payload, 
                settings.SECRET_KEY, 
                algorithm='HS256'
            )
            
            return {
                'access_token': access_token,
                'expires_in': 3600,
                'token_type': 'Bearer'
            }
            
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
        except Exception as e:
            raise AuthenticationFailed('Invalid refresh token')
    
    @staticmethod
    def _get_user_data(user):
        """Extract user data for JWT payload"""
        if hasattr(user, 'patient_profile'):
            return {
                'user_type': 'patient',
                'patient_id': user.patient_profile.patient_id,
                'is_profile_complete': user.patient_profile.is_profile_complete,
                'permissions': ['view_own_records', 'book_appointments', 'view_own_prescriptions']
            }
        elif hasattr(user, 'personnel_profile'):
            # Get roles
            roles = list(user.personnel_profile.role_assignments.filter(
                is_active=True
            ).values_list('role__name', flat=True))
            
            # Get permissions based on roles
            permissions = CustomJWTHandler._get_personnel_permissions(user.personnel_profile)
            
            return {
                'user_type': 'personnel',
                'employee_id': user.personnel_profile.employee_id,
                'is_verified': user.personnel_profile.is_verified,
                'verification_status': user.personnel_profile.verification_status,
                'roles': roles,
                'permissions': permissions,
                'can_trigger_emergency': any(
                    user.personnel_profile.role_assignments.filter(
                        role__can_trigger_emergency=True,
                        is_active=True
                    )
                )
            }
        else:
            return {
                'user_type': 'unknown',
                'permissions': []
            }
    
    @staticmethod
    def _get_personnel_permissions(personnel):
        """Get personnel permissions based on roles"""
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


class CustomJWTAuthentication(BaseAuthentication):
    """Custom JWT authentication class for DRF"""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
        
        try:
            # Extract token from "Bearer <token>" format
            auth_parts = auth_header.split(' ')
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                return None
            
            token = auth_parts[1]
            
            # Decode token
            payload = CustomJWTHandler.decode_token(token)
            
            if payload.get('type') != 'access':
                raise AuthenticationFailed('Invalid token type')
            
            # Get user
            user_id = payload.get('user_id')
            user = User.objects.get(id=user_id, is_active=True)
            
            # Add token payload to user object for easy access in views
            user.token_payload = payload
            
            return (user, token)
            
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
        except AuthenticationFailed:
            raise
        except Exception:
            raise AuthenticationFailed('Invalid token')
    
    def authenticate_header(self, request):
        return 'Bearer'


class JWTTokenBlacklist:
    """Simple token blacklist using cache or database"""
    
    @staticmethod
    def blacklist_token(token):
        """Add token to blacklist"""
        from django.core.cache import cache
        
        try:
            payload = CustomJWTHandler.decode_token(token)
            token_id = f"blacklisted_token_{payload.get('user_id')}_{payload.get('iat')}"
            
            # Cache until token would naturally expire
            exp_time = payload.get('exp')
            if exp_time:
                exp_datetime = datetime.fromtimestamp(exp_time)
                cache_timeout = max(0, int((exp_datetime - datetime.utcnow()).total_seconds()))
                cache.set(token_id, True, timeout=cache_timeout)
                
        except Exception:
            pass  # If token is invalid, no need to blacklist
    
    @staticmethod
    def is_token_blacklisted(token):
        """Check if token is blacklisted"""
        from django.core.cache import cache
        
        try:
            payload = CustomJWTHandler.decode_token(token)
            token_id = f"blacklisted_token_{payload.get('user_id')}_{payload.get('iat')}"
            return cache.get(token_id, False)
        except Exception:
            return True  # If token is invalid, consider it blacklisted
