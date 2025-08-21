from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

def require_permissions(*permissions):
    """Decorator to require specific permissions"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self, request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                return Response({
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get user permissions from token
            token_payload = getattr(request.user, 'token_payload', {})
            user_permissions = set(token_payload.get('permissions', []))
            required_permissions = set(permissions)
            
            # Check if user has all required permissions
            if not required_permissions.issubset(user_permissions):
                missing_permissions = required_permissions - user_permissions
                return Response({
                    'error': 'Insufficient permissions',
                    'missing_permissions': list(missing_permissions)
                }, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(self, request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_user_type(user_type):
    """Decorator to require specific user type"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(self, request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                return Response({
                    'error': 'Authentication required'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Get user type from token
            token_payload = getattr(request.user, 'token_payload', {})
            current_user_type = token_payload.get('user_type')
            
            if current_user_type != user_type:
                return Response({
                    'error': f'Access restricted to {user_type} users only'
                }, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(self, request, *args, **kwargs)
        return wrapped_view
    return decorator


def require_verified_personnel(view_func):
    """Decorator to require verified personnel"""
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get verification status from token
        token_payload = getattr(request.user, 'token_payload', {})
        
        if token_payload.get('user_type') != 'personnel':
            return Response({
                'error': 'Access restricted to personnel only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not token_payload.get('is_verified', False):
            return Response({
                'error': 'Account verification required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(self, request, *args, **kwargs)
    return wrapped_view


def emergency_access_required(view_func):
    """Decorator for emergency access only"""
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return Response({
                'error': 'Authentication required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Get permissions from token
        token_payload = getattr(request.user, 'token_payload', {})
        user_permissions = token_payload.get('permissions', [])
        
        if 'emergency_override' not in user_permissions:
            return Response({
                'error': 'Emergency access privileges required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if user can trigger emergency
        if not token_payload.get('can_trigger_emergency', False):
            return Response({
                'error': 'Emergency override capability required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(self, request, *args, **kwargs)
    return wrapped_view


def log_emergency_access(view_func):
    """Decorator to log emergency access attempts"""
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        from .models import EmergencyAccess
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get user info from token
        token_payload = getattr(request.user, 'token_payload', {})
        
        # Log the emergency access attempt
        logger.warning(f"Emergency access attempted by {token_payload.get('email')} "
                      f"({token_payload.get('employee_id')}) from IP {request.META.get('REMOTE_ADDR')}")
        
        try:
            response = view_func(self, request, *args, **kwargs)
            
            # If successful, log the success
            if response.status_code < 400:
                logger.info(f"Emergency access granted to {token_payload.get('email')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Emergency access error for {token_payload.get('email')}: {str(e)}")
            raise
        
    return wrapped_view
