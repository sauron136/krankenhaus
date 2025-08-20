from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
from authentication.permissions import IsPersonnel, IsPatient, IsPersonnelOrPatient
from .models import (
    Medication,
    Prescription,
    PrescriptionItem,
    PharmacyDispensing,
    MedicationAdministration
)
from .serializers import (
    MedicationSerializer,
    MedicationCreateSerializer,
    PrescriptionListSerializer,
    PrescriptionDetailSerializer,
    PrescriptionCreateSerializer,
    PrescriptionItemSerializer,
    PharmacyDispensingSerializer,
    PharmacyDispensingCreateSerializer,
    MedicationAdministrationSerializer,
    MedicationAdministrationCreateSerializer,
    MedicationAdministrationUpdateSerializer
)
from appointments.models import Appointment

class MedicationListView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        medications = Medication.objects.filter(is_active=True)
        
        search = request.query_params.get('search')
        if search:
            medications = medications.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search) |
                Q(brand_name__icontains=search)
            )
        
        serializer = MedicationSerializer(medications, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = MedicationCreateSerializer(data=request.data)
        if serializer.is_valid():
            medication = serializer.save()
            result_serializer = MedicationSerializer(medication)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MedicationDetailView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request, medication_id):
        try:
            medication = Medication.objects.get(id=medication_id)
        except Medication.DoesNotExist:
            return Response(
                {'error': 'Medication not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MedicationSerializer(medication)
        return Response(serializer.data)

class PrescriptionListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        if hasattr(request.user, 'prescriptions'):  # Patient
            prescriptions = Prescription.objects.filter(patient=request.user, is_active=True)
        else:  # Personnel
            prescriptions = Prescription.objects.filter(is_active=True)
            
            patient_id = request.query_params.get('patient_id')
            if patient_id:
                prescriptions = prescriptions.filter(patient_id=patient_id)
            
            doctor_id = request.query_params.get('doctor_id')
            if doctor_id:
                prescriptions = prescriptions.filter(doctor_id=doctor_id)
            
            date_from = request.query_params.get('date_from')
            if date_from:
                prescriptions = prescriptions.filter(prescription_date__gte=date_from)
            
            date_to = request.query_params.get('date_to')
            if date_to:
                prescriptions = prescriptions.filter(prescription_date__lte=date_to)
        
        prescriptions = prescriptions.order_by('-prescription_date')
        serializer = PrescriptionListSerializer(prescriptions, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if hasattr(request.user, 'prescriptions'):  # Patient trying to create
            return Response(
                {'error': 'Patients cannot create prescriptions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PrescriptionCreateSerializer(data=request.data)
        if serializer.is_valid():
            appointment_id = serializer.validated_data['appointment'].id
            try:
                appointment = Appointment.objects.get(id=appointment_id)
            except Appointment.DoesNotExist:
                return Response(
                    {'error': 'Appointment not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            prescription = serializer.save(
                patient=appointment.patient,
                doctor=request.user
            )
            
            result_serializer = PrescriptionDetailSerializer(prescription)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PrescriptionDetailView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get_prescription(self, prescription_id, user):
        try:
            prescription = Prescription.objects.get(id=prescription_id)
            
            if hasattr(user, 'prescriptions') and prescription.patient != user:
                return None
            
            return prescription
        except Prescription.DoesNotExist:
            return None
    
    def get(self, request, prescription_id):
        prescription = self.get_prescription(prescription_id, request.user)
        if not prescription:
            return Response(
                {'error': 'Prescription not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = PrescriptionDetailSerializer(prescription)
        return Response(serializer.data)

class PharmacyDispensingView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        dispensings = PharmacyDispensing.objects.all()
        
        prescription_id = request.query_params.get('prescription_id')
        if prescription_id:
            dispensings = dispensings.filter(prescription_item__prescription_id=prescription_id)
        
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            dispensings = dispensings.filter(prescription_item__prescription__patient_id=patient_id)
        
        dispensings = dispensings.order_by('-dispensed_at')
        serializer = PharmacyDispensingSerializer(dispensings, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = PharmacyDispensingCreateSerializer(data=request.data)
        if serializer.is_valid():
            dispensing = serializer.save(dispensed_by=request.user)
            result_serializer = PharmacyDispensingSerializer(dispensing)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MedicationAdministrationListView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        administrations = MedicationAdministration.objects.all()
        
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            administrations = administrations.filter(patient_id=patient_id)
        
        scheduled_date = request.query_params.get('scheduled_date')
        if scheduled_date:
            administrations = administrations.filter(scheduled_time__date=scheduled_date)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            administrations = administrations.filter(status=status_filter)
        
        administered_by = request.query_params.get('administered_by')
        if administered_by:
            administrations = administrations.filter(administered_by_id=administered_by)
        
        serializer = MedicationAdministrationSerializer(administrations, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = MedicationAdministrationCreateSerializer(data=request.data)
        if serializer.is_valid():
            administration = serializer.save()
            result_serializer = MedicationAdministrationSerializer(administration)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MedicationAdministrationDetailView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request, administration_id):
        try:
            administration = MedicationAdministration.objects.get(id=administration_id)
        except MedicationAdministration.DoesNotExist:
            return Response(
                {'error': 'Administration record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MedicationAdministrationSerializer(administration)
        return Response(serializer.data)
    
    def patch(self, request, administration_id):
        try:
            administration = MedicationAdministration.objects.get(id=administration_id)
        except MedicationAdministration.DoesNotExist:
            return Response(
                {'error': 'Administration record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MedicationAdministrationUpdateSerializer(
            administration, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            if 'status' in serializer.validated_data and serializer.validated_data['status'] == 'administered':
                serializer.validated_data['administered_by'] = request.user
                if not serializer.validated_data.get('actual_time'):
                    serializer.validated_data['actual_time'] = timezone.now()
            
            updated_administration = serializer.save()
            result_serializer = MedicationAdministrationSerializer(updated_administration)
            return Response(result_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MyAdministrationsView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        administrations = MedicationAdministration.objects.filter(
            administered_by=request.user
        ).order_by('-actual_time')
        
        serializer = MedicationAdministrationSerializer(administrations, many=True)
        return Response(serializer.data)
