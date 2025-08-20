from django.urls import path
from . import views

urlpatterns = [
    # Medical records overview
    path('records/', views.MedicalRecordListView.as_view(), name='medical-record-list'),
    path('records/<int:record_id>/', views.MedicalRecordDetailView.as_view(), name='medical-record-detail'),
    path('patients/<int:patient_id>/summary/', views.PatientMedicalSummaryView.as_view(), name='patient-medical-summary'),
    
    # Allergies
    path('records/<int:record_id>/allergies/', views.AllergyListView.as_view(), name='allergy-list'),
    
    # Medical history
    path('records/<int:record_id>/history/', views.MedicalHistoryListView.as_view(), name='medical-history-list'),
    
    # Encounters
    path('encounters/', views.EncounterListView.as_view(), name='encounter-list'),
    path('encounters/<int:encounter_id>/', views.EncounterDetailView.as_view(), name='encounter-detail'),
    
    # Clinical notes
    path('encounters/<int:encounter_id>/notes/', views.ClinicalNoteListView.as_view(), name='clinical-note-list'),
    path('notes/<int:note_id>/', views.ClinicalNoteDetailView.as_view(), name='clinical-note-detail'),
    path('notes/<int:note_id>/sign/', views.SignClinicalNoteView.as_view(), name='sign-clinical-note'),
    
    # Vital signs
    path('encounters/<int:encounter_id>/vitals/', views.VitalSignsListView.as_view(), name='vital-signs-list'),
    
    # Audit trail
    path('records/<int:record_id>/access-log/', views.RecordAccessLogView.as_view(), name='record-access-log'),
]
