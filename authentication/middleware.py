from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .jwt_handler import JWTTokenBlacklist
import json

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Middleware to handle JWT token blacklist checking"""
    
    def process_request(self, request):
        # Skip for certain paths
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/api/auth/register/',
            '/api/auth/login/',
            '/api/auth/verify-email/',
            '/api/auth/password/reset/',
        ]
        
        if any(request.path.startswith(path) for path in skip_paths):
            return None
        
        # Check for blacklisted tokens
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            if JWTTokenBlacklist.is_token_blacklisted(token):
                return JsonResponse({
                    'error': 'Token has been revoked',
                    'code': 'TOKEN_REVOKED'
                }, status=401)
        
        return None
