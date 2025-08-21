from django.urls import path
from .views import (
    # Patient Profile Views
    PatientProfileView,
    PatientProfileUpdateView,
    PatientSearchView,
    PatientDetailView,
    
    # Personnel Profile Views
    PersonnelProfileView,
    PersonnelProfileUpdateView,
    PersonnelSearchView,
    PersonnelDetailView,
    PersonnelVerificationView,
    
    # Emergency Access Views
    EmergencyPatientAccessView,
    EmergencyAccessLogView,
)

app_name = 'accounts'

urlpatterns = [
    # Patient Profile Management
    path('patient/profile/', PatientProfileView.as_view(), name='patient-profile'),
    path('patient/profile/update/', PatientProfileUpdateView.as_view(), name='patient-profile-update'),
    path('patient/search/', PatientSearchView.as_view(), name='patient-search'),
    path('patient/<str:patient_id>/', PatientDetailView.as_view(), name='patient-detail'),
    
    # Personnel Profile Management
    path('personnel/profile/', PersonnelProfileView.as_view(), name='personnel-profile'),
    path('personnel/profile/update/', PersonnelProfileUpdateView.as_view(), name='personnel-profile-update'),
    path('personnel/search/', PersonnelSearchView.as_view(), name='personnel-search'),
    path('personnel/<str:employee_id>/', PersonnelDetailView.as_view(), name='personnel-detail'),
    path('personnel/verification/', PersonnelVerificationView.as_view(), name='personnel-verification'),
    
    # Emergency Access
    path('emergency/patient-access/', EmergencyPatientAccessView.as_view(), name='emergency-patient-access'),
    path('emergency/access-log/', EmergencyAccessLogView.as_view(), name='emergency-access-log'),
]
