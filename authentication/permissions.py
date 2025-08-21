from rest_framework import permissions

class HasPermission(permissions.BasePermission):
    """Custom permission class that checks JWT token permissions"""
    
    def __init__(self, required_permission):
        self.required_permission = required_permission
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get permissions from token payload
        token_payload = getattr(request.user, 'token_payload', {})
        user_permissions = token_payload.get('permissions', [])
        
        return self.required_permission in user_permissions


class IsPatient(permissions.BasePermission):
    """Permission for patient-only access"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        token_payload = getattr(request.user, 'token_payload', {})
        return token_payload.get('user_type') == 'patient'


class IsPersonnel(permissions.BasePermission):
    """Permission for personnel-only access"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        token_payload = getattr(request.user, 'token_payload', {})
        return token_payload.get('user_type') == 'personnel'


class IsVerifiedPersonnel(permissions.BasePermission):
    """Permission for verified personnel only"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        token_payload = getattr(request.user, 'token_payload', {})
        return (
            token_payload.get('user_type') == 'personnel' and
            token_payload.get('is_verified', False)
        )


class CanTriggerEmergency(permissions.BasePermission):
    """Permission for personnel who can trigger emergency overrides"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        token_payload = getattr(request.user, 'token_payload', {})
        return (
            token_payload.get('user_type') == 'personnel' and
            token_payload.get('can_trigger_emergency', False)
        )


class HasRole(permissions.BasePermission):
    """Permission class that checks if user has specific role"""
    
    def __init__(self, required_role):
        self.required_role = required_role
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        token_payload = getattr(request.user, 'token_payload', {})
        user_roles = token_payload.get('roles', [])
        
        return self.required_role in user_roles


# Helper functions to create permission instances
def require_permission(permission_name):
    """Factory function to create HasPermission instances"""
    return HasPermission(permission_name)

def require_role(role_name):
    """Factory function to create HasRole instances"""
    return HasRole(role_name)
