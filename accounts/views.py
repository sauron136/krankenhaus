from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Patient, Personnel, Role, EmergencyAccess
from .serializers import (
    PatientProfileSerializer,
    PatientUpdateSerializer,
    PersonnelProfileSerializer,
    PersonnelUpdateSerializer,
    PersonnelVerificationSerializer,
    EmergencyAccessSerializer,
)
from authentication.permissions import (
    IsPatient, IsPersonnel, IsVerifiedPersonnel, 
    CanTriggerEmergency, require_role, require_permission
)
from authentication.jwt_handler import CustomJWTHandler


class PatientProfileView(APIView):
    """View patient's own profile"""
    permission_classes = [IsAuthenticated, IsPatient]
    
    def get(self, request):
        try:
            patient = Patient.objects.select_related('user').get(user=request.user)
            serializer = PatientProfileSerializer(patient)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PatientProfileUpdateView(APIView):
    """Update patient's own profile"""
    permission_classes = [IsAuthenticated, IsPatient]
    
    def put(self, request):
        try:
            patient = Patient.objects.get(user=request.user)
            serializer = PatientUpdateSerializer(patient, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        'message': 'Profile updated successfully',
                        'data': PatientProfileSerializer(patient).data
                    },
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PatientSearchView(APIView):
    """Search patients by various criteria (Verified Personnel only)"""
    permission_classes = [IsAuthenticated, IsVerifiedPersonnel]
    
    def get(self, request):
        query = request.GET.get('q', '')
        patient_id = request.GET.get('patient_id', '')
        
        if patient_id:
            # Direct patient ID lookup
            try:
                patient = Patient.objects.get_by_patient_id(patient_id)
                serializer = PatientProfileSerializer(patient)
                return Response([serializer.data], status=status.HTTP_200_OK)
            except Patient.DoesNotExist:
                return Response([], status=status.HTTP_200_OK)
        
        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Search by name, phone, email
        patients = Patient.objects.search_patients(query)[:20]  # Limit results
        serializer = PatientProfileSerializer(patients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientDetailView(APIView):
    """Get patient details by patient ID (Verified Personnel only)"""
    permission_classes = [IsAuthenticated, IsVerifiedPersonnel]
    
    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get_by_patient_id(patient_id)
            
            # Check access level based on personnel role from token
            token_payload = getattr(request.user, 'token_payload', {})
            user_roles = token_payload.get('roles', [])
            serializer_data = PatientProfileSerializer(patient).data
            
            # Filter data based on role permissions
            if any(role in user_roles for role in ['Receptionist', 'Security']):
                # Limited access - only basic info
                limited_data = {
                    'patient_id': serializer_data['patient_id'],
                    'user': {
                        'first_name': serializer_data['user']['first_name'],
                        'last_name': serializer_data['user']['last_name'],
                        'email': serializer_data['user']['email'],
                    },
                    'phone_number': serializer_data.get('phone_number'),
                    'date_of_birth': serializer_data.get('date_of_birth'),
                }
                return Response(limited_data, status=status.HTTP_200_OK)
            
            # Full access for medical personnel
            return Response(serializer_data, status=status.HTTP_200_OK)
            
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PersonnelProfileView(APIView):
    """View personnel's own profile"""
    permission_classes = [IsAuthenticated, IsPersonnel]
    
    def get(self, request):
        try:
            personnel = Personnel.objects.select_related('user', 'role').get(user=request.user)
            serializer = PersonnelProfileSerializer(personnel)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Personnel.DoesNotExist:
            return Response(
                {'error': 'Personnel profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PersonnelProfileUpdateView(APIView):
    """Update personnel's own profile"""
    permission_classes = [IsAuthenticated, IsPersonnel]
    
    def put(self, request):
        try:
            personnel = Personnel.objects.get(user=request.user)
            serializer = PersonnelUpdateSerializer(personnel, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        'message': 'Profile updated successfully',
                        'data': PersonnelProfileSerializer(personnel).data
                    },
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Personnel.DoesNotExist:
            return Response(
                {'error': 'Personnel profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PersonnelSearchView(APIView):
    """Search personnel (Admin only)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Only admins can search all personnel - using token payload
        token_payload = getattr(request.user, 'token_payload', {})
        user_roles = token_payload.get('roles', [])
        
        if 'Admin' not in user_roles:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        query = request.GET.get('q', '')
        role = request.GET.get('role', '')
        
        if len(query) < 2:
            return Response(
                {'error': 'Search query must be at least 2 characters'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        personnel = Personnel.objects.search_personnel(query)
        
        if role:
            personnel = personnel.filter(role__name=role)
        
        personnel = personnel[:20]  # Limit results
        serializer = PersonnelProfileSerializer(personnel, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PersonnelDetailView(APIView):
    """Get personnel details by employee ID (Admin only)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, employee_id):
        # Only admins can view other personnel details - using token payload
        token_payload = getattr(request.user, 'token_payload', {})
        user_roles = token_payload.get('roles', [])
        
        if 'Admin' not in user_roles:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            personnel = Personnel.objects.select_related('user', 'role').get(employee_id=employee_id)
            serializer = PersonnelProfileSerializer(personnel)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Personnel.DoesNotExist:
            return Response(
                {'error': 'Personnel not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class PersonnelVerificationView(APIView):
    """Handle personnel verification by admin"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Only admins can verify personnel - using token payload
        token_payload = getattr(request.user, 'token_payload', {})
        user_roles = token_payload.get('roles', [])
        
        if 'Admin' not in user_roles:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PersonnelVerificationSerializer(data=request.data)
        if serializer.is_valid():
            employee_id = serializer.validated_data['employee_id']
            action = serializer.validated_data['action']
            role_id = serializer.validated_data.get('role_id')
            
            try:
                personnel = Personnel.objects.get(employee_id=employee_id)
                
                if action == 'verify':
                    personnel.is_verified = True
                    if role_id:
                        role = get_object_or_404(Role, id=role_id)
                        personnel.role = role
                    personnel.save()
                    
                    return Response(
                        {'message': 'Personnel verified successfully'},
                        status=status.HTTP_200_OK
                    )
                    
                elif action == 'reject':
                    personnel.is_verified = False
                    personnel.save()
                    
                    return Response(
                        {'message': 'Personnel verification rejected'},
                        status=status.HTTP_200_OK
                    )
                    
            except Personnel.DoesNotExist:
                return Response(
                    {'error': 'Personnel not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmergencyPatientAccessView(APIView):
    """Emergency access to patient data"""
    permission_classes = [IsAuthenticated, CanTriggerEmergency]
    
    def post(self, request):
        patient_search = request.data.get('patient_search', {})
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'error': 'Emergency reason is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find patient by various methods
        patient = None
        search_method = None
        
        if patient_search.get('patient_id'):
            try:
                patient = Patient.objects.get_by_patient_id(patient_search['patient_id'])
                search_method = 'patient_id'
            except Patient.DoesNotExist:
                pass
        
        if not patient and patient_search.get('name') and patient_search.get('dob'):
            patients = Patient.objects.emergency_search(
                patient_search['name'], 
                patient_search['dob']
            )
            if patients.exists():
                patient = patients.first()
                search_method = 'name_dob'
        
        if not patient:
            return Response(
                {'error': 'Patient not found with provided information'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Log emergency access
        EmergencyAccess.objects.create(
            patient=patient,
            personnel=request.user.personnel,
            reason=reason,
            search_method=search_method,
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        
        # Return patient data
        serializer = PatientProfileSerializer(patient)
        return Response(
            {
                'message': 'Emergency access granted',
                'patient_data': serializer.data,
                'warning': 'This emergency access has been logged for audit purposes'
            },
            status=status.HTTP_200_OK
        )


class EmergencyAccessLogView(APIView):
    """View emergency access logs (Admin only)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Only admins can view emergency access logs - using token payload
        token_payload = getattr(request.user, 'token_payload', {})
        user_roles = token_payload.get('roles', [])
        
        if 'Admin' not in user_roles:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = EmergencyAccess.objects.select_related(
            'patient__user', 'personnel__user'
        ).order_by('-accessed_at')[:100]  # Last 100 emergency accesses
        
        serializer = EmergencyAccessSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
