from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
from authentication.permissions import IsPersonnel, IsPatient, IsPersonnelOrPatient
from .models import (
    Department, 
    AppointmentType, 
    ProviderAvailability, 
    Appointment, 
    AppointmentStatusHistory
)
from .serializers import (
    DepartmentSerializer,
    AppointmentTypeSerializer,
    ProviderAvailabilitySerializer,
    ProviderAvailabilityCreateSerializer,
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentSearchSerializer,
    AppointmentStatusHistorySerializer,
    ProviderBasicSerializer
)
from accounts.models import Personnel

class DepartmentListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        departments = Department.objects.filter(is_active=True)
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

class AppointmentTypeListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        appointment_types = AppointmentType.objects.filter(is_active=True)
        serializer = AppointmentTypeSerializer(appointment_types, many=True)
        return Response(serializer.data)

class ProviderListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        # Get personnel who can provide medical services
        medical_roles = [
            'Doctor', 'Surgeon', 'Cardiologist', 'Neurologist', 
            'Pediatrician', 'Anesthesiologist', 'Nurse', 'ICU_Nurse',
            'Emergency_Nurse', 'Pediatric_Nurse', 'OR_Nurse', 'Midwife', 'Radiologist'
        ]
        
        providers = Personnel.objects.filter(
            role_assignments__role__name__in=medical_roles,
            role_assignments__is_active=True,
            is_active=True
        ).distinct()
        
        department_id = request.query_params.get('department')
        if department_id:
            # Filter by department if needed (you might need to add department to Personnel model)
            pass
        
        serializer = ProviderBasicSerializer(providers, many=True)
        return Response(serializer.data)

class ProviderAvailabilityView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        provider_id = request.query_params.get('provider_id')
        if provider_id:
            availability = ProviderAvailability.objects.filter(
                provider_id=provider_id, 
                is_active=True
            )
        else:
            availability = ProviderAvailability.objects.filter(
                provider=request.user,
                is_active=True
            )
        
        serializer = ProviderAvailabilitySerializer(availability, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ProviderAvailabilityCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Default to current user if no provider specified
            if 'provider' not in serializer.validated_data:
                serializer.validated_data['provider'] = request.user
            
            availability = serializer.save()
            result_serializer = ProviderAvailabilitySerializer(availability)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppointmentListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        # Patients can only see their own appointments
        if hasattr(request.user, 'appointments'):  # Patient
            appointments = Appointment.objects.filter(patient=request.user)
        else:  # Personnel
            appointments = Appointment.objects.all()
            
            # Apply filters
            provider_id = request.query_params.get('provider_id')
            if provider_id:
                appointments = appointments.filter(provider_id=provider_id)
            
            department_id = request.query_params.get('department_id')
            if department_id:
                appointments = appointments.filter(department_id=department_id)
            
            status_filter = request.query_params.get('status')
            if status_filter:
                appointments = appointments.filter(status=status_filter)
            
            date_from = request.query_params.get('date_from')
            if date_from:
                appointments = appointments.filter(appointment_date__gte=date_from)
            
            date_to = request.query_params.get('date_to')
            if date_to:
                appointments = appointments.filter(appointment_date__lte=date_to)
        
        appointments = appointments.order_by('appointment_date', 'appointment_time')
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Set the creator
            appointment = serializer.save(created_by=request.user)
            
            # Create status history entry
            AppointmentStatusHistory.objects.create(
                appointment=appointment,
                old_status='',
                new_status='scheduled',
                changed_by=request.user,
                reason='Appointment created'
            )
            
            result_serializer = AppointmentDetailSerializer(appointment)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppointmentDetailView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get_appointment(self, appointment_id, user):
        try:
            appointment = Appointment.objects.get(id=appointment_id)
            
            # Patients can only view their own appointments
            if hasattr(user, 'appointments') and appointment.patient != user:
                return None
            
            return appointment
        except Appointment.DoesNotExist:
            return None
    
    def get(self, request, appointment_id):
        appointment = self.get_appointment(appointment_id, request.user)
        if not appointment:
            return Response(
                {'error': 'Appointment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AppointmentDetailSerializer(appointment)
        return Response(serializer.data)
    
    def put(self, request, appointment_id):
        appointment = self.get_appointment(appointment_id, request.user)
        if not appointment:
            return Response(
                {'error': 'Appointment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only personnel can update appointments (or patients for limited fields)
        if hasattr(request.user, 'appointments'):  # Patient
            return Response(
                {'error': 'Patients cannot update appointments. Please contact the hospital.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            updated_appointment = serializer.save()
            result_serializer = AppointmentDetailSerializer(updated_appointment)
            return Response(result_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, appointment_id):
        appointment = self.get_appointment(appointment_id, request.user)
        if not appointment:
            return Response(
                {'error': 'Appointment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only personnel can delete appointments
        if hasattr(request.user, 'appointments'):  # Patient
            return Response(
                {'error': 'Patients cannot delete appointments. Please contact the hospital.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete by changing status to cancelled
        if appointment.status not in ['cancelled', 'completed']:
            old_status = appointment.status
            appointment.status = 'cancelled'
            appointment.save()
            
            # Create status history
            AppointmentStatusHistory.objects.create(
                appointment=appointment,
                old_status=old_status,
                new_status='cancelled',
                changed_by=request.user,
                reason='Appointment cancelled by staff'
            )
            
            return Response({'message': 'Appointment cancelled successfully'})
        else:
            return Response(
                {'error': 'Cannot cancel appointment with current status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class AppointmentStatusUpdateView(APIView):
    permission_classes = [IsPersonnel]
    
    def patch(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AppointmentStatusUpdateSerializer(appointment, data=request.data, partial=True)
        if serializer.is_valid():
            old_status = appointment.status
            new_status = serializer.validated_data['status']
            reason = serializer.validated_data.get('reason', '')
            
            # Update appointment status
            appointment.status = new_status
            appointment.save()
            
            # Create status history entry
            AppointmentStatusHistory.objects.create(
                appointment=appointment,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                reason=reason
            )
            
            result_serializer = AppointmentDetailSerializer(appointment)
            return Response(result_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AppointmentSearchView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        serializer = AppointmentSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        appointments = Appointment.objects.all()
        
        # Apply search filters
        patient_name = serializer.validated_data.get('patient_name')
        if patient_name:
            appointments = appointments.filter(
                Q(patient__first_name__icontains=patient_name) |
                Q(patient__last_name__icontains=patient_name)
            )
        
        provider_id = serializer.validated_data.get('provider_id')
        if provider_id:
            appointments = appointments.filter(provider_id=provider_id)
        
        department_id = serializer.validated_data.get('department_id')
        if department_id:
            appointments = appointments.filter(department_id=department_id)
        
        status_filter = serializer.validated_data.get('status')
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        
        date_from = serializer.validated_data.get('date_from')
        if date_from:
            appointments = appointments.filter(appointment_date__gte=date_from)
        
        date_to = serializer.validated_data.get('date_to')
        if date_to:
            appointments = appointments.filter(appointment_date__lte=date_to)
        
        appointment_type_id = serializer.validated_data.get('appointment_type_id')
        if appointment_type_id:
            appointments = appointments.filter(appointment_type_id=appointment_type_id)
        
        priority = serializer.validated_data.get('priority')
        if priority:
            appointments = appointments.filter(priority=priority)
        
        appointments = appointments.order_by('appointment_date', 'appointment_time')
        result_serializer = AppointmentListSerializer(appointments, many=True)
        return Response(result_serializer.data)

class MyAppointmentsView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        """Get appointments where the current user is the provider"""
        appointments = Appointment.objects.filter(
            provider=request.user
        ).order_by('appointment_date', 'appointment_time')
        
        # Filter by date range if provided
        date_from = request.query_params.get('date_from')
        if date_from:
            appointments = appointments.filter(appointment_date__gte=date_from)
        
        date_to = request.query_params.get('date_to')
        if date_to:
            appointments = appointments.filter(appointment_date__lte=date_to)
        
        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            appointments = appointments.filter(status=status_filter)
        
        serializer = AppointmentListSerializer(appointments, many=True)
        return Response(serializer.data)

class AppointmentHistoryView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        history = AppointmentStatusHistory.objects.filter(
            appointment=appointment
        ).order_by('-changed_at')
        
        serializer = AppointmentStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
