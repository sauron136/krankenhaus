import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from ..models import CustomJWTToken
from accounts.models import Personnel, Patient

class JWTService:
    
    @staticmethod
    def get_secret_key():
        return getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
    
    @staticmethod
    def get_access_token_lifetime():
        return getattr(settings, 'JWT_ACCESS_TOKEN_LIFETIME', timedelta(minutes=30))
    
    @staticmethod
    def get_refresh_token_lifetime():
        return getattr(settings, 'JWT_REFRESH_TOKEN_LIFETIME', timedelta(days=7))
    
    @classmethod
    def generate_token_pair(cls, user, request=None):
        """Generate access and refresh token pair for user"""
        now = timezone.now()
        
        # Determine user type
        is_personnel = isinstance(user, Personnel)
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'user_type': 'personnel' if is_personnel else 'patient',
            'exp': now + cls.get_access_token_lifetime(),
            'iat': now,
            'token_type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'user_type': 'personnel' if is_personnel else 'patient',
            'exp': now + cls.get_refresh_token_lifetime(),
            'iat': now,
            'token_type': 'refresh'
        }
        
        # Generate JWT tokens
        access_token = jwt.encode(access_payload, cls.get_secret_key(), algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, cls.get_secret_key(), algorithm='HS256')
        
        # Get request info
        ip_address = None
        user_agent = ''
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Save to database
        access_token_obj = CustomJWTToken.objects.create(
            personnel=user if is_personnel else None,
            patient=user if not is_personnel else None,
            token=access_token,
            token_type='access',
            expires_at=now + cls.get_access_token_lifetime(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        refresh_token_obj = CustomJWTToken.objects.create(
            personnel=user if is_personnel else None,
            patient=user if not is_personnel else None,
            token=refresh_token,
            token_type='refresh',
            expires_at=now + cls.get_refresh_token_lifetime(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'access_expires_at': access_token_obj.expires_at,
            'refresh_expires_at': refresh_token_obj.expires_at
        }
    
    @classmethod
    def validate_token(cls, token):
        """Validate and decode JWT token"""
        try:
            # Decode token
            payload = jwt.decode(token, cls.get_secret_key(), algorithms=['HS256'])
            
            # Check if token exists in database and is active
            token_obj = CustomJWTToken.objects.get(
                token=token, 
                is_active=True
            )
            
            # Update last_used
            token_obj.last_used = timezone.now()
            token_obj.save(update_fields=['last_used'])
            
            return payload, token_obj
            
        except jwt.ExpiredSignatureError:
            raise Exception('Token has expired')
        except jwt.InvalidTokenError:
            raise Exception('Invalid token')
        except CustomJWTToken.DoesNotExist:
            raise Exception('Token not found or inactive')
    
    @classmethod
    def refresh_access_token(cls, refresh_token, request=None):
        """Generate new access token using refresh token"""
        try:
            payload, token_obj = cls.validate_token(refresh_token)
            
            if payload['token_type'] != 'refresh':
                raise Exception('Invalid token type')
            
            # Get user
            user = token_obj.user
            if not user:
                raise Exception('User not found')
            
            # Generate new access token
            now = timezone.now()
            is_personnel = isinstance(user, Personnel)
            
            access_payload = {
                'user_id': user.id,
                'user_type': 'personnel' if is_personnel else 'patient',
                'exp': now + cls.get_access_token_lifetime(),
                'iat': now,
                'token_type': 'access'
            }
            
            access_token = jwt.encode(access_payload, cls.get_secret_key(), algorithm='HS256')
            
            # Get request info
            ip_address = None
            user_agent = ''
            if request:
                ip_address = cls.get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Save new access token
            access_token_obj = CustomJWTToken.objects.create(
                personnel=user if is_personnel else None,
                patient=user if not is_personnel else None,
                token=access_token,
                token_type='access',
                expires_at=now + cls.get_access_token_lifetime(),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return {
                'access_token': access_token,
                'expires_at': access_token_obj.expires_at
            }
            
        except Exception as e:
            raise e
    
    @classmethod
    def revoke_token(cls, token):
        """Revoke/deactivate token"""
        try:
            token_obj = CustomJWTToken.objects.get(token=token)
            token_obj.is_active = False
            token_obj.save(update_fields=['is_active'])
            return True
        except CustomJWTToken.DoesNotExist:
            return False
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """Remove expired tokens from database"""
        now = timezone.now()
        expired_count = CustomJWTToken.objects.filter(expires_at__lt=now).delete()[0]
        return expired_count
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
