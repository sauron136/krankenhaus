from rest_framework import serializers
from .models import (
    TestCategory,
    LabTest,
    LabOrder,
    LabOrderItem,
    Sample,
    LabResult,
    CriticalValue
)
from accounts.serializers import PersonnelBasicSerializer, PatientBasicSerializer
from appointments.serializers import AppointmentBasicSerializer

class TestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCategory
        fields = '__all__'

class LabTestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = LabTest
        fields = '__all__'

class LabTestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        exclude = ['created_at']

class LabOrderItemSerializer(serializers.ModelSerializer):
    test_display = serializers.CharField(source='get_test_display', read_only=True)
    lab_test_details = LabTestSerializer(source='lab_test', read_only=True)
    
    class Meta:
        model = LabOrderItem
        fields = '__all__'

class LabOrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabOrderItem
        exclude = ['status', 'is_active']

class LabOrderListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    ordered_by_name = serializers.CharField(source='ordered_by.get_full_name', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    appointment_details = AppointmentBasicSerializer(source='appointment', read_only=True)
    
    class Meta:
        model = LabOrder
        fields = [
            'id', 'order_date', 'priority', 'patient_name', 'ordered_by_name',
            'items_count', 'appointment_details', 'clinical_indication', 'is_active'
        ]

class LabOrderDetailSerializer(serializers.ModelSerializer):
    patient = PatientBasicSerializer(read_only=True)
    ordered_by = PersonnelBasicSerializer(read_only=True)
    appointment = AppointmentBasicSerializer(read_only=True)
    items = LabOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = LabOrder
        fields = '__all__'

class LabOrderCreateSerializer(serializers.ModelSerializer):
    items = LabOrderItemCreateSerializer(many=True)
    
    class Meta:
        model = LabOrder
        exclude = ['patient', 'ordered_by', 'created_at']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        lab_order = LabOrder.objects.create(**validated_data)
        
        for item_data in items_data:
            LabOrderItem.objects.create(lab_order=lab_order, **item_data)
        
        return lab_order

class SampleSerializer(serializers.ModelSerializer):
    order_item_details = LabOrderItemSerializer(source='order_item', read_only=True)
    collected_by_name = serializers.CharField(source='collected_by.get_full_name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.get_full_name', read_only=True)
    
    class Meta:
        model = Sample
        fields = '__all__'

class SampleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        exclude = ['collected_by', 'received_by', 'created_at']

class SampleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sample
        fields = [
            'received_at', 'received_by', 'status', 'rejection_reason',
            'volume_collected', 'container_type', 'notes'
        ]

class LabResultSerializer(serializers.ModelSerializer):
    order_item_details = LabOrderItemSerializer(source='order_item', read_only=True)
    sample_details = SampleSerializer(source='sample', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='order_item.lab_order.patient.get_full_name', read_only=True)
    
    class Meta:
        model = LabResult
        fields = '__all__'

class LabResultCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        exclude = ['performed_by', 'reviewed_by', 'created_at', 'updated_at']

class LabResultUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = [
            'result_value', 'unit', 'reference_range', 'abnormal_flag',
            'status', 'performed_at', 'reviewed_at', 'interpretation', 'comments'
        ]

class CriticalValueSerializer(serializers.ModelSerializer):
    result_details = LabResultSerializer(source='result', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.get_full_name', read_only=True)
    notified_personnel_details = PersonnelBasicSerializer(source='notified_personnel', many=True, read_only=True)
    
    class Meta:
        model = CriticalValue
        fields = '__all__'

class LabResultSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for result lists"""
    test_name = serializers.CharField(source='order_item.get_test_display', read_only=True)
    patient_name = serializers.CharField(source='order_item.lab_order.patient.get_full_name', read_only=True)
    order_date = serializers.DateTimeField(source='order_item.lab_order.order_date', read_only=True)
    
    class Meta:
        model = LabResult
        fields = [
            'id', 'test_name', 'patient_name', 'order_date', 'result_value',
            'unit', 'abnormal_flag', 'status', 'performed_at'
        ]
