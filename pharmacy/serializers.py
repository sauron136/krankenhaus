from rest_framework import serializers
from .models import (
    Medication, 
    Prescription, 
    PrescriptionItem, 
    PharmacyDispensing, 
    MedicationAdministration
)
from accounts.serializers import PersonnelBasicSerializer, PatientBasicSerializer
from appointments.serializers import AppointmentBasicSerializer

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'

class MedicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        exclude = ['created_at']

class PrescriptionItemSerializer(serializers.ModelSerializer):
    medication_display = serializers.CharField(source='get_medication_display', read_only=True)
    medication_details = MedicationSerializer(source='medication', read_only=True)
    
    class Meta:
        model = PrescriptionItem
        fields = '__all__'

class PrescriptionItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        exclude = ['is_active']

class PrescriptionListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    appointment_details = AppointmentBasicSerializer(source='appointment', read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'prescription_date', 'patient_name', 'doctor_name', 
            'items_count', 'appointment_details', 'is_active'
        ]

class PrescriptionDetailSerializer(serializers.ModelSerializer):
    patient = PatientBasicSerializer(read_only=True)
    doctor = PersonnelBasicSerializer(read_only=True)
    appointment = AppointmentBasicSerializer(read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Prescription
        fields = '__all__'

class PrescriptionCreateSerializer(serializers.ModelSerializer):
    items = PrescriptionItemCreateSerializer(many=True)
    
    class Meta:
        model = Prescription
        exclude = ['patient', 'doctor', 'created_at']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        prescription = Prescription.objects.create(**validated_data)
        
        for item_data in items_data:
            PrescriptionItem.objects.create(prescription=prescription, **item_data)
        
        return prescription

class PharmacyDispensingSerializer(serializers.ModelSerializer):
    prescription_item_details = PrescriptionItemSerializer(source='prescription_item', read_only=True)
    dispensed_by_name = serializers.CharField(source='dispensed_by.get_full_name', read_only=True)
    
    class Meta:
        model = PharmacyDispensing
        fields = '__all__'

class PharmacyDispensingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyDispensing
        exclude = ['dispensed_by', 'dispensed_at']

class MedicationAdministrationSerializer(serializers.ModelSerializer):
    prescription_item_details = PrescriptionItemSerializer(source='prescription_item', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    administered_by_name = serializers.CharField(source='administered_by.get_full_name', read_only=True)
    
    class Meta:
        model = MedicationAdministration
        fields = '__all__'

class MedicationAdministrationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationAdministration
        exclude = ['administered_by', 'created_at', 'updated_at']

class MedicationAdministrationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationAdministration
        fields = ['actual_time', 'dose_given', 'status', 'notes']

