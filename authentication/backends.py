from django.contrib.auth.backends import BaseBackend
from accounts.models import Personnel, Patient
from .services.jwt_service import JWTService

class JWTAuthenticationBackend(BaseBackend):
    def authenticate(self, request, token=None, **kwargs):
        if not token:
            return None
        
        try:
            payload, token_obj = JWTService.validate_token(token)
            user_id = payload.get('user_id')
            user_type = payload.get('user_type')
            
            if user_type == 'personnel':
                user = Personnel.objects.get(id=user_id, is_active=True)
            elif user_type == 'patient':
                user = Patient.objects.get(id=user_id, is_active=True)
            else:
                return None
                
            return user
        except Exception:
            return None
    
    def get_user(self, user_id):
        # Try Personnel first, then Patient
        try:
            return Personnel.objects.get(pk=user_id, is_active=True)
        except Personnel.DoesNotExist:
            try:
                return Patient.objects.get(pk=user_id, is_active=True)
            except Patient.DoesNotExist:
                return None
