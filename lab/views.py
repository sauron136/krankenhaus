from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
from authentication.permissions import IsPersonnel, IsPatient, IsPersonnelOrPatient
from .models import (
    TestCategory,
    LabTest,
    LabOrder,
    LabOrderItem,
    Sample,
    LabResult,
    CriticalValue
)
from .serializers import (
    TestCategorySerializer,
    LabTestSerializer,
    LabTestCreateSerializer,
    LabOrderListSerializer,
    LabOrderDetailSerializer,
    LabOrderCreateSerializer,
    LabOrderItemSerializer,
    SampleSerializer,
    SampleCreateSerializer,
    SampleUpdateSerializer,
    LabResultSerializer,
    LabResultCreateSerializer,
    LabResultUpdateSerializer,
    LabResultSummarySerializer,
    CriticalValueSerializer
)
from appointments.models import Appointment

class TestCategoryListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        categories = TestCategory.objects.filter(is_active=True)
        serializer = TestCategorySerializer(categories, many=True)
        return Response(serializer.data)

class LabTestListView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        tests = LabTest.objects.filter(is_active=True)
        
        category_id = request.query_params.get('category_id')
        if category_id:
            tests = tests.filter(category_id=category_id)
        
        search = request.query_params.get('search')
        if search:
            tests = tests.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        
        specimen_type = request.query_params.get('specimen_type')
        if specimen_type:
            tests = tests.filter(specimen_type=specimen_type)
        
        serializer = LabTestSerializer(tests, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = LabTestCreateSerializer(data=request.data)
        if serializer.is_valid():
            test = serializer.save()
            result_serializer = LabTestSerializer(test)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LabTestDetailView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request, test_id):
        try:
            test = LabTest.objects.get(id=test_id)
        except LabTest.DoesNotExist:
            return Response(
                {'error': 'Lab test not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LabTestSerializer(test)
        return Response(serializer.data)

class LabOrderListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        if hasattr(request.user, 'lab_orders'):  # Patient
            orders = LabOrder.objects.filter(patient=request.user, is_active=True)
        else:  # Personnel
            orders = LabOrder.objects.filter(is_active=True)
            
            patient_id = request.query_params.get('patient_id')
            if patient_id:
                orders = orders.filter(patient_id=patient_id)
            
            ordered_by_id = request.query_params.get('ordered_by_id')
            if ordered_by_id:
                orders = orders.filter(ordered_by_id=ordered_by_id)
            
            priority = request.query_params.get('priority')
            if priority:
                orders = orders.filter(priority=priority)
            
            date_from = request.query_params.get('date_from')
            if date_from:
                orders = orders.filter(order_date__gte=date_from)
            
            date_to = request.query_params.get('date_to')
            if date_to:
                orders = orders.filter(order_date__lte=date_to)
        
        orders = orders.order_by('-order_date')
        serializer = LabOrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if hasattr(request.user, 'lab_orders'):  # Patient trying to create
            return Response(
                {'error': 'Patients cannot create lab orders'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LabOrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            appointment_id = serializer.validated_data['appointment'].id
            try:
                appointment = Appointment.objects.get(id=appointment_id)
            except Appointment.DoesNotExist:
                return Response(
                    {'error': 'Appointment not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            lab_order = serializer.save(
                patient=appointment.patient,
                ordered_by=request.user
            )
            
            result_serializer = LabOrderDetailSerializer(lab_order)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LabOrderDetailView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get_lab_order(self, order_id, user):
        try:
            lab_order = LabOrder.objects.get(id=order_id)
            
            if hasattr(user, 'lab_orders') and lab_order.patient != user:
                return None
            
            return lab_order
        except LabOrder.DoesNotExist:
            return None
    
    def get(self, request, order_id):
        lab_order = self.get_lab_order(order_id, request.user)
        if not lab_order:
            return Response(
                {'error': 'Lab order not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LabOrderDetailSerializer(lab_order)
        return Response(serializer.data)

class SampleListView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        samples = Sample.objects.all()
        
        order_id = request.query_params.get('order_id')
        if order_id:
            samples = samples.filter(order_item__lab_order_id=order_id)
        
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            samples = samples.filter(order_item__lab_order__patient_id=patient_id)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            samples = samples.filter(status=status_filter)
        
        collected_date = request.query_params.get('collected_date')
        if collected_date:
            samples = samples.filter(collected_at__date=collected_date)
        
        samples = samples.order_by('-collected_at')
        serializer = SampleSerializer(samples, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SampleCreateSerializer(data=request.data)
        if serializer.is_valid():
            sample = serializer.save(collected_by=request.user)
            
            # Update order item status
            order_item = sample.order_item
            order_item.status = 'sample_collected'
            order_item.save()
            
            result_serializer = SampleSerializer(sample)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SampleDetailView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request, sample_id):
        try:
            sample = Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return Response(
                {'error': 'Sample not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SampleSerializer(sample)
        return Response(serializer.data)
    
    def patch(self, request, sample_id):
        try:
            sample = Sample.objects.get(id=sample_id)
        except Sample.DoesNotExist:
            return Response(
                {'error': 'Sample not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = SampleUpdateSerializer(sample, data=request.data, partial=True)
        if serializer.is_valid():
            if 'status' in serializer.validated_data:
                new_status = serializer.validated_data['status']
                if new_status == 'received' and not serializer.validated_data.get('received_at'):
                    serializer.validated_data['received_at'] = timezone.now()
                    serializer.validated_data['received_by'] = request.user
                
                # Update order item status
                if new_status == 'received':
                    sample.order_item.status = 'in_progress'
                    sample.order_item.save()
                elif new_status == 'rejected':
                    sample.order_item.status = 'sample_pending'
                    sample.order_item.save()
            
            updated_sample = serializer.save()
            result_serializer = SampleSerializer(updated_sample)
            return Response(result_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LabResultListView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get(self, request):
        if hasattr(request.user, 'lab_orders'):  # Patient
            results = LabResult.objects.filter(
                order_item__lab_order__patient=request.user,
                status='final'
            )
        else:  # Personnel
            results = LabResult.objects.all()
            
            patient_id = request.query_params.get('patient_id')
            if patient_id:
                results = results.filter(order_item__lab_order__patient_id=patient_id)
            
            status_filter = request.query_params.get('status')
            if status_filter:
                results = results.filter(status=status_filter)
            
            abnormal_flag = request.query_params.get('abnormal_flag')
            if abnormal_flag:
                results = results.filter(abnormal_flag=abnormal_flag)
            
            date_from = request.query_params.get('date_from')
            if date_from:
                results = results.filter(created_at__gte=date_from)
            
            date_to = request.query_params.get('date_to')
            if date_to:
                results = results.filter(created_at__lte=date_to)
        
        results = results.order_by('-created_at')
        serializer = LabResultSummarySerializer(results, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        if hasattr(request.user, 'lab_orders'):  # Patient trying to create
            return Response(
                {'error': 'Patients cannot create lab results'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LabResultCreateSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save(performed_by=request.user, performed_at=timezone.now())
            
            # Update order item status
            result.order_item.status = 'completed'
            result.order_item.save()
            
            # Check for critical values
            if result.abnormal_flag in ['critical_high', 'critical_low']:
                CriticalValue.objects.create(result=result)
            
            result_serializer = LabResultSerializer(result)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LabResultDetailView(APIView):
    permission_classes = [IsPersonnelOrPatient]
    
    def get_lab_result(self, result_id, user):
        try:
            result = LabResult.objects.get(id=result_id)
            
            if hasattr(user, 'lab_orders') and result.order_item.lab_order.patient != user:
                return None
            
            return result
        except LabResult.DoesNotExist:
            return None
    
    def get(self, request, result_id):
        result = self.get_lab_result(result_id, request.user)
        if not result:
            return Response(
                {'error': 'Lab result not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = LabResultSerializer(result)
        return Response(serializer.data)
    
    def patch(self, request, result_id):
        result = self.get_lab_result(result_id, request.user)
        if not result:
            return Response(
                {'error': 'Lab result not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if hasattr(request.user, 'lab_orders'):  # Patient trying to update
            return Response(
                {'error': 'Patients cannot update lab results'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LabResultUpdateSerializer(result, data=request.data, partial=True)
        if serializer.is_valid():
            if 'status' in serializer.validated_data:
                if serializer.validated_data['status'] == 'final' and not result.reviewed_at:
                    serializer.validated_data['reviewed_at'] = timezone.now()
                    serializer.validated_data['reviewed_by'] = request.user
            
            updated_result = serializer.save()
            result_serializer = LabResultSerializer(updated_result)
            return Response(result_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CriticalValuesView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        critical_values = CriticalValue.objects.filter(
            acknowledged_at__isnull=True
        ).order_by('-notification_sent_at')
        
        serializer = CriticalValueSerializer(critical_values, many=True)
        return Response(serializer.data)

class CriticalValueDetailView(APIView):
    permission_classes = [IsPersonnel]
    
    def patch(self, request, critical_id):
        try:
            critical_value = CriticalValue.objects.get(id=critical_id)
        except CriticalValue.DoesNotExist:
            return Response(
                {'error': 'Critical value not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        critical_value.acknowledged_at = timezone.now()
        critical_value.acknowledged_by = request.user
        critical_value.action_taken = request.data.get('action_taken', '')
        critical_value.save()
        
        serializer = CriticalValueSerializer(critical_value)
        return Response(serializer.data)

class PendingOrdersView(APIView):
    permission_classes = [IsPersonnel]
    
    def get(self, request):
        """Get orders that need attention"""
        pending_items = LabOrderItem.objects.filter(
            status__in=['ordered', 'sample_pending', 'sample_collected', 'in_progress'],
            is_active=True
        ).select_related('lab_order__patient', 'lab_order__ordered_by')
        
        serializer = LabOrderItemSerializer(pending_items, many=True)
        return Response(serializer.data)
