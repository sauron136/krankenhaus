from rest_framework import serializers
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
from accounts.serializers import PersonnelBasicSerializer, PatientBasicSerializer
from appointments.serializers import AppointmentBasicSerializer, DepartmentSerializer

class AllergySerializer(serializers.ModelSerializer):
    identified_by_name = serializers.CharField(source='identified_by.get_full_name', read_only=True)
    
    class Meta:
        model = Allergy
        fields = '__all__'

class AllergyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergy
        exclude = ['medical_record', 'identified_by']

class MedicalHistorySerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    
    class Meta:
        model = MedicalHistory
        fields = '__all__'

class MedicalHistoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        exclude = ['medical_record', 'recorded_by', 'recorded_at']

class VitalSignsSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    
    class Meta:
        model = VitalSigns
        fields = '__all__'

class VitalSignsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSigns
        exclude = ['encounter', 'recorded_by', 'recorded_at', 'bmi']

class DiagnosisSerializer(serializers.ModelSerializer):
    diagnosed_by_name = serializers.CharField(source='diagnosed_by.get_full_name', read_only=True)
    
    class Meta:
        model = Diagnosis
        fields = '__all__'

class DiagnosisCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        exclude = ['encounter', 'diagnosed_by', 'diagnosis_date']

class TreatmentPlanSerializer(serializers.ModelSerializer):
    prescribed_by_name = serializers.CharField(source='prescribed_by.get_full_name', read_only=True)
    
    class Meta:
        model = TreatmentPlan
        fields = '__all__'

class TreatmentPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentPlan
        exclude = ['encounter', 'prescribed_by', 'created_at', 'updated_at']

class ClinicalNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    
    class Meta:
        model = ClinicalNote
        fields = '__all__'

class ClinicalNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalNote
        exclude = ['encounter', 'author', 'created_at', 'updated_at', 'is_signed', 'signed_at']

class ClinicalNoteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalNote
        fields = ['subjective', 'objective', 'assessment', 'plan', 'additional_notes']

class EncounterListSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    patient_name = serializers.CharField(source='medical_record.patient.get_full_name', read_only=True)
    
    class Meta:
        model = Encounter
        fields = [
            'id', 'encounter_type', 'encounter_date', 'provider_name',
            'department_name', 'patient_name', 'chief_complaint'
        ]

class EncounterDetailSerializer(serializers.ModelSerializer):
    provider = PersonnelBasicSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    appointment = AppointmentBasicSerializer(read_only=True)
    
    vital_signs = VitalSignsSerializer(many=True, read_only=True)
    clinical_notes = ClinicalNoteSerializer(many=True, read_only=True)
    diagnoses = DiagnosisSerializer(many=True, read_only=True)
    treatment_plans = TreatmentPlanSerializer(many=True, read_only=True)
    
    class Meta:
        model = Encounter
        fields = '__all__'

class EncounterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter
        exclude = ['medical_record', 'provider', 'created_at', 'updated_at']

class MedicalRecordSummarySerializer(serializers.ModelSerializer):
    patient = PatientBasicSerializer(read_only=True)
    allergies_count = serializers.IntegerField(source='allergies.count', read_only=True)
    encounters_count = serializers.IntegerField(source='encounters.count', read_only=True)
    
    class Meta:
        model = MedicalRecord
        fields = [
            'id', 'patient', 'blood_type', 'allergies_count', 
            'encounters_count', 'created_at', 'updated_at'
        ]

class MedicalRecordDetailSerializer(serializers.ModelSerializer):
    patient = PatientBasicSerializer(read_only=True)
    allergies = AllergySerializer(many=True, read_only=True)
    medical_history = MedicalHistorySerializer(many=True, read_only=True)
    
    # Recent encounters (last 5)
    recent_encounters = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecord
        fields = '__all__'
    
    def get_recent_encounters(self, obj):
        recent = obj.encounters.all()[:5]
        return EncounterListSerializer(recent, many=True).data

class PatientMedicalSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for patient medical overview"""
    patient = PatientBasicSerializer(read_only=True)
    active_allergies = serializers.SerializerMethodField()
    chronic_conditions = serializers.SerializerMethodField()
    last_encounter = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalRecord
        fields = ['id', 'patient', 'blood_type', 'active_allergies', 'chronic_conditions', 'last_encounter']
    
    def get_active_allergies(self, obj):
        allergies = obj.allergies.filter(is_active=True)[:3]  # Top 3
        return [f"{allergy.allergen} ({allergy.severity})" for allergy in allergies]
    
    def get_chronic_conditions(self, obj):
        conditions = obj.medical_history.filter(
            condition_type='chronic_condition', 
            is_ongoing=True
        )[:3]  # Top 3
        return [condition.condition for condition in conditions]
    
    def get_last_encounter(self, obj):
        last = obj.encounters.first()
        if last:
            return {
                'date': last.encounter_date,
                'type': last.encounter_type,
                'provider': last.provider.get_full_name(),
                'chief_complaint': last.chief_complaint
            }
        return None

class RecordAccessSerializer(serializers.ModelSerializer):
    accessed_by_name = serializers.CharField(source='accessed_by.get_full_name', read_only=True)
    patient_name = serializers.CharField(source='medical_record.patient.get_full_name', read_only=True)
    
    class Meta:
        model = RecordAccess
        fields = ['id', 'accessed_by_name', 'patient_name', 'access_type', 'accessed_at']
