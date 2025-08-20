from django.urls import path
from .views import (
    PersonnelProfileView,
    PatientProfileView,
    PersonnelSearchView,
    PersonnelManagementView,
    RoleManagementView,
    AssignRoleView
)

app_name = 'accounts'

urlpatterns = [
    # Profile Management
    path('personnel/profile/', PersonnelProfileView.as_view(), name='personnel-profile'),
    path('patient/profile/', PatientProfileView.as_view(), name='patient-profile'),
    
    # Search & Listing
    path('personnel/search/', PersonnelSearchView.as_view(), name='personnel-search'),
    
    # Personnel Management
    path('personnel/', PersonnelManagementView.as_view(), name='personnel-list-create'),
    
    # Role Management
    path('roles/', RoleManagementView.as_view(), name='role-list-create'),
    path('roles/assign/', AssignRoleView.as_view(), name='assign-role'),
]
