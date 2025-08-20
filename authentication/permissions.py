from rest_framework.permissions import BasePermission
from accounts.models import Personnel, Patient

class IsPersonnel(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and isinstance(request.user, Personnel)

class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and isinstance(request.user, Patient)

class IsPersonnelOrPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            isinstance(request.user, Personnel) or isinstance(request.user, Patient)
        )

class HasRole(BasePermission):
    required_roles = []
    
    def has_permission(self, request, view):
        if not isinstance(request.user, Personnel):
            return False
        
        if hasattr(view, 'required_roles'):
            required_roles = view.required_roles
        else:
            required_roles = self.required_roles
        
        if not required_roles:
            return True
        
        user_roles = request.user.role_assignments.filter(
            is_active=True
        ).values_list('role__name', flat=True)
        
        return any(role in user_roles for role in required_roles)
