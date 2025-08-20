from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from authentication.permissions import IsPersonnel, IsPatient, IsPersonnelOrPatient, HasRole
from .models import Personnel, Patient, Role, PersonnelRole
from .serializers import (
    PersonnelProfileSerializer,
    PatientProfileSerializer,
    PersonnelUpdateSerializer,
    PatientUpdateSerializer,
    PersonnelListSerializer,
    PersonnelCreateSerializer,
    RoleSerializer,
    AssignRoleSerializer,
    PersonnelSearchSerializer
)

class PersonnelProfileView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        serializer = PersonnelProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = PersonnelUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientProfileView(APIView):
    permission_classes = [IsPatient]
    
    def get(self, request):
        serializer = PatientProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = PatientUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PersonnelSearchView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        serializer = PersonnelSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = Personnel.objects.all()
        
        # Apply filters based on search parameters
        query = serializer.validated_data.get('query')
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(username__icontains=query) |
                Q(employee_id__icontains=query)
            )
        
        role = serializer.validated_data.get('role')
        if role:
            queryset = queryset.filter(role_assignments__role__name__icontains=role, role_assignments__is_active=True)
        
        is_active = serializer.validated_data.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
        
        hire_date_from = serializer.validated_data.get('hire_date_from')
        if hire_date_from:
            queryset = queryset.filter(hire_date__gte=hire_date_from)
        
        hire_date_to = serializer.validated_data.get('hire_date_to')
        if hire_date_to:
            queryset = queryset.filter(hire_date__lte=hire_date_to)
        
        queryset = queryset.distinct()
        result_serializer = PersonnelListSerializer(queryset, many=True)
        return Response(result_serializer.data)

class PersonnelManagementView(APIView):
    permission_classes = [HasRole]
    required_roles = ['HR_Manager', 'Admin', 'Department_Head']
    
    def get(self, request):
        personnel = Personnel.objects.all()
        serializer = PersonnelListSerializer(personnel, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = PersonnelCreateSerializer(data=request.data)
        if serializer.is_valid():
            personnel = serializer.save()
            result_serializer = PersonnelProfileSerializer(personnel)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleManagementView(APIView):
    permission_classes = [HasRole]
    required_roles = ['HR_Manager', 'Admin']
    
    def get(self, request):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            role = serializer.save()
            return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignRoleView(APIView):
    permission_classes = [HasRole]
    required_roles = ['HR_Manager', 'Admin', 'Department_Head']
    
    def post(self, request):
        serializer = AssignRoleSerializer(data=request.data)
        if serializer.is_valid():
            try:
                personnel = Personnel.objects.get(id=serializer.validated_data['personnel_id'])
                role = Role.objects.get(id=serializer.validated_data['role_id'])
                
                # Check if assignment already exists
                existing = PersonnelRole.objects.filter(
                    personnel=personnel, 
                    role=role
                ).first()
                
                if existing:
                    if existing.is_active:
                        return Response({
                            'error': 'Personnel already has this role assigned'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # Reactivate existing assignment
                        existing.is_active = True
                        existing.assigned_by = request.user
                        existing.expires_date = serializer.validated_data.get('expires_date')
                        existing.notes = serializer.validated_data.get('notes', '')
                        existing.save()
                        assignment = existing
                else:
                    # Create new assignment
                    assignment = PersonnelRole.objects.create(
                        personnel=personnel,
                        role=role,
                        assigned_by=request.user,
                        expires_date=serializer.validated_data.get('expires_date'),
                        notes=serializer.validated_data.get('notes', '')
                    )
                
                return Response({
                    'message': 'Role assigned successfully',
                    'assignment_id': assignment.id
                }, status=status.HTTP_201_CREATED)
                
            except Personnel.DoesNotExist:
                return Response({'error': 'Personnel not found'}, status=status.HTTP_404_NOT_FOUND)
            except Role.DoesNotExist:
                return Response({'error': 'Role not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
