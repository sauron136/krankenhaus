from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
from authentication.permissions import IsPersonnel, IsPatient, IsPersonnelOrPatient
from .models import (
    MedicalRecord,
    Allergy,
    MedicalHistory,
    Encounter,
    VitalSigns,
    ClinicalNote,
    Diagnosis,
    TreatmentPlan,
    RecordAccess
)
from .serializers import (
    MedicalRecordSummarySerializer,
    MedicalRecordDetailSerializer,
    PatientMedicalSummarySerializer,
    AllergySerializer,
    AllergyCreateSerializer,
    MedicalHistorySerializer,
    MedicalHistoryCreateSerializer,
    EncounterListSerializer,
    EncounterDetailSerializer,
    EncounterCreateSerializer,
    VitalSignsSerializer,
    VitalSignsCreateSerializer,
    ClinicalNoteSerializer,
    ClinicalNoteCreateSerializer,
    ClinicalNoteUpdateSerializer,
    DiagnosisSerializer,
    DiagnosisCreateSerializer,
    TreatmentPlanSerializer,
    TreatmentPlanCreateSerializer,
    RecordAccessSerializer
)
from appointments.models import Appointment
from accounts.models import Patient

def log_record_access(medical_record, user, access_type, request):
    """Helper function to log record access for audit trail"""
    RecordAccess.objects.create(
        medical_record=medical_record,
        accessed_by=user,
        access_type=access_type,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

class MedicalRecordListView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        medical_records = MedicalRecord.objects.all()
        
        patient_search = request.query_params.get('patient_search')
        if patient_search:
            medical_records = medical_records.filter(
                Q(patient__first_name__icontains=patient_search) |
                Q(patient__last_name__icontains=patient_search) |
                Q(patient__email__icontains=patient_search)
            )
        
        serializer = MedicalRecordSummarySerializer(medical_records, many=True)
        return Response(serializer.data)

class MedicalRecordDetailView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get_medical_record(self, record_id, user):
        try:
            medical_record = MedicalRecord.objects.get(id=record_id)
            
            # Patients can only access their own records
            if hasattr(user, 'medical_record') and medical_record.patient != user:
                return None
            
            return medical_record
        except MedicalRecord.DoesNotExist:
            return None
    
    def get(self, request, record_id):
        medical_record = self.get_medical_record(record_id, request.user)
        if not medical_record:
            return Response(
                {'error': 'Medical record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log access for audit trail (only for personnel accessing records)
        if not hasattr(request.user, 'medical_record'):
            log_record_access(medical_record, request.user, 'view', request)
        
        serializer = MedicalRecordDetailSerializer(medical_record)
        return Response(serializer.data)

class PatientMedicalSummaryView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(id=patient_id)
            medical_record, created = MedicalRecord.objects.get_or_create(patient=patient)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        log_record_access(medical_record, request.user, 'view', request)
        serializer = PatientMedicalSummarySerializer(medical_record)
        return Response(serializer.data)

class AllergyListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request, record_id):
        try:
            medical_record = MedicalRecord.objects.get(id=record_id)
            
            if hasattr(request.user, 'medical_record') and medical_record.patient != request.user:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'Medical record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        allergies = medical_record.allergies.filter(is_active=True)
        serializer = AllergySerializer(allergies, many=True)
        return Response(serializer.data)
    
    def post(self, request, record_id):
        if hasattr(request.user, 'medical_record'):
            return Response(
                {'error': 'Patients cannot add allergies. Please contact medical staff.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            medical_record = MedicalRecord.objects.get(id=record_id)
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'Medical record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AllergyCreateSerializer(data=request.data)
        if serializer.is_valid():
            allergy = serializer.save(
                medical_record=medical_record,
                identified_by=request.user
            )
            
            log_record_access(medical_record, request.user, 'edit', request)
            result_serializer = AllergySerializer(allergy)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MedicalHistoryListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request, record_id):
        try:
            medical_record = MedicalRecord.objects.get(id=record_id)
            
            if hasattr(request.user, 'medical_record') and medical_record.patient != request.user:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'Medical record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        history = medical_record.medical_history.all().order_by('-recorded_at')
        serializer = MedicalHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    def post(self, request, record_id):
        if hasattr(request.user, 'medical_record'):
            return Response(
                {'error': 'Patients cannot add medical history. Please contact medical staff.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            medical_record = MedicalRecord.objects.get(id=record_id)
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'Medical record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MedicalHistoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            history = serializer.save(
                medical_record=medical_record,
                recorded_by=request.user
            )
            
            log_record_access(medical_record, request.user, 'edit', request)
            result_serializer = MedicalHistorySerializer(history)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EncounterListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        if hasattr(request.user, 'medical_record'):  # Patient
            encounters = Encounter.objects.filter(medical_record__patient=request.user)
        else:  # Personnel
            encounters = Encounter.objects.all()
            
            patient_id = request.query_params.get('patient_id')
            if patient_id:
                encounters = encounters.filter(medical_record__patient_id=patient_id)
            
            provider_id = request.query_params.get('provider_id')
            if provider_id:
                encounters = encounters.filter(provider_id=provider_id)
            
            encounter_type = request.query_params.get('encounter_type')
            if encounter_type:
                encounters = encounters.filter(encounter_type=encounter_type)
            
            date_from = request.query_params.get('date_from')
            if date_from:
                encounters = encounters.filter(encounter_date__gte=date_from)
            
            date_to = request.query_params.get('date_to')
            if date_to:
                encounters = encounters.filter(encounter_date__lte=date_to)
        
        encounters = encounters.order_by('-encounter_date')
        serializer = EncounterListSerializer(encounters, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if hasattr(request.user, 'medical_record'):
            return Response(
                {'error': 'Patients cannot create encounters'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = EncounterCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Get or create medical record for patient
            appointment_id = serializer.validated_data.get('appointment')
            if appointment_id:
                try:
                    appointment = Appointment.objects.get(id=appointment_id.id)
                    medical_record, created = MedicalRecord.objects.get_or_create(
                        patient=appointment.patient
                    )
                except Appointment.DoesNotExist:
                    return Response(
                        {'error': 'Appointment not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {'error': 'Appointment is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            encounter = serializer.save(
                medical_record=medical_record,
                provider=request.user
            )
            
            log_record_access(medical_record, request.user, 'create', request)
            result_serializer = EncounterDetailSerializer(encounter)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EncounterDetailView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get_encounter(self, encounter_id, user):
        try:
            encounter = Encounter.objects.get(id=encounter_id)
            
            if hasattr(user, 'medical_record') and encounter.medical_record.patient != user:
                return None
            
            return encounter
        except Encounter.DoesNotExist:
            return None
    
    def get(self, request, encounter_id):
        encounter = self.get_encounter(encounter_id, request.user)
        if not encounter:
            return Response(
                {'error': 'Encounter not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log access
        if not hasattr(request.user, 'medical_record'):
            log_record_access(encounter.medical_record, request.user, 'view', request)
        
        serializer = EncounterDetailSerializer(encounter)
        return Response(serializer.data)

class ClinicalNoteListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request, encounter_id):
        try:
            encounter = Encounter.objects.get(id=encounter_id)
            
            if hasattr(request.user, 'medical_record') and encounter.medical_record.patient != request.user:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Encounter.DoesNotExist:
            return Response(
                {'error': 'Encounter not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        notes = encounter.clinical_notes.all().order_by('-created_at')
        serializer = ClinicalNoteSerializer(notes, many=True)
        return Response(serializer.data)
    
    def post(self, request, encounter_id):
        if hasattr(request.user, 'medical_record'):
            return Response(
                {'error': 'Patients cannot create clinical notes'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            encounter = Encounter.objects.get(id=encounter_id)
        except Encounter.DoesNotExist:
            return Response(
                {'error': 'Encounter not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClinicalNoteCreateSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.save(
                encounter=encounter,
                author=request.user
            )
            
            log_record_access(encounter.medical_record, request.user, 'edit', request)
            result_serializer = ClinicalNoteSerializer(note)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClinicalNoteDetailView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request, note_id):
        try:
            note = ClinicalNote.objects.get(id=note_id)
            
            if hasattr(request.user, 'medical_record') and note.encounter.medical_record.patient != request.user:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except ClinicalNote.DoesNotExist:
            return Response(
                {'error': 'Clinical note not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClinicalNoteSerializer(note)
        return Response(serializer.data)
    
    def patch(self, request, note_id):
        try:
            note = ClinicalNote.objects.get(id=note_id)
            
            if hasattr(request.user, 'medical_record'):
                return Response(
                    {'error': 'Patients cannot edit clinical notes'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Only allow author to edit unsigned notes
            if note.is_signed:
                return Response(
                    {'error': 'Cannot edit signed notes'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if note.author != request.user:
                return Response(
                    {'error': 'You can only edit your own notes'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
                
        except ClinicalNote.DoesNotExist:
            return Response(
                {'error': 'Clinical note not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ClinicalNoteUpdateSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            updated_note = serializer.save()
            log_record_access(note.encounter.medical_record, request.user, 'edit', request)
            result_serializer = ClinicalNoteSerializer(updated_note)
            return Response(result_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignClinicalNoteView(APIView):
    permission_classes = [IsPersonnel]
    
    def post(self, request, note_id):
        try:
            note = ClinicalNote.objects.get(id=note_id, author=request.user)
        except ClinicalNote.DoesNotExist:
            return Response(
                {'error': 'Note not found or you are not the author'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if note.is_signed:
            return Response(
                {'error': 'Note is already signed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        note.is_signed = True
        note.signed_at = timezone.now()
        note.save()
        
        serializer = ClinicalNoteSerializer(note)
        return Response(serializer.data)

class VitalSignsListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request, encounter_id):
        try:
            encounter = Encounter.objects.get(id=encounter_id)
            
            if hasattr(request.user, 'medical_record') and encounter.medical_record.patient != request.user:
                return Response(
                    {'error': 'Access denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        except Encounter.DoesNotExist:
            return Response(
                {'error': 'Encounter not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        vitals = encounter.vital_signs.all().order_by('-recorded_at')
        serializer = VitalSignsSerializer(vitals, many=True)
        return Response(serializer.data)
    
    def post(self, request, encounter_id):
        if hasattr(request.user, 'medical_record'):
            return Response(
                {'error': 'Patients cannot record vital signs'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            encounter = Encounter.objects.get(id=encounter_id)
        except Encounter.DoesNotExist:
            return Response(
                {'error': 'Encounter not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = VitalSignsCreateSerializer(data=request.data)
        if serializer.is_valid():
            vitals = serializer.save(
                encounter=encounter,
                recorded_by=request.user
            )
            
            log_record_access(encounter.medical_record, request.user, 'edit', request)
            result_serializer = VitalSignsSerializer(vitals)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RecordAccessLogView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request, record_id):
        try:
            medical_record = MedicalRecord.objects.get(id=record_id)
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'Medical record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        access_logs = medical_record.access_logs.all().order_by('-accessed_at')[:50]  # Last 50 accesses
        serializer = RecordAccessSerializer(access_logs, many=True)
        return Response(serializer.data)
