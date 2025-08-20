from django.urls import path
from . import views

urlpatterns = [
    # Medication management
    path('medications/', views.MedicationListView.as_view(), name='medication-list'),
    path('medications/<int:medication_id>/', views.MedicationDetailView.as_view(), name='medication-detail'),
    
    # Prescription management
    path('prescriptions/', views.PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/<int:prescription_id>/', views.PrescriptionDetailView.as_view(), name='prescription-detail'),
    
    # Pharmacy dispensing (outpatient)
    path('dispensing/', views.PharmacyDispensingView.as_view(), name='pharmacy-dispensing'),
    
    # Medication administration (inpatient)
    path('administrations/', views.MedicationAdministrationListView.as_view(), name='medication-administration-list'),
    path('administrations/<int:administration_id>/', views.MedicationAdministrationDetailView.as_view(), name='medication-administration-detail'),
    path('my-administrations/', views.MyAdministrationsView.as_view(), name='my-administrations'),
]
