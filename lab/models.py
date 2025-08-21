from django.db import models

from .managers import LabTestTypeManager, LabOrderManager  # Import managers

class LabTestType(models.Model):
    objects = LabTestTypeManager()  # Assign the custom manager

    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    normal_range = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    sample_type = models.CharField(max_length=100, choices=[
        ('blood', 'Blood'),
        ('urine', 'Urine'),
        ('stool', 'Stool'),
        ('saliva', 'Saliva'),
        ('tissue', 'Tissue'),
        ('other', 'Other'),
    ])
    preparation_instructions = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class LabOrder(models.Model):
    objects = LabOrderManager()  # Assign the custom manager

    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='lab_orders')
    ordered_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='lab_orders_created')
    medical_record = models.ForeignKey('medical_records.MedicalRecord', on_delete=models.CASCADE, related_name='lab_orders')
    
    order_number = models.CharField(max_length=50, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    
    priority = models.CharField(max_length=20, choices=[
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
    ], default='routine')
    
    status = models.CharField(max_length=20, choices=[
        ('ordered', 'Ordered'),
        ('collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='ordered')
    
    clinical_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Lab Order {self.order_number} for {self.patient.patient_id}"

class LabOrderItem(models.Model):
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='test_items')
    test_type = models.ForeignKey(LabTestType, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='pending')
    
    def __str__(self):
        return f"{self.test_type.name} for order {self.lab_order.order_number}"

class LabResult(models.Model):
    lab_order_item = models.OneToOneField(LabOrderItem, on_delete=models.CASCADE, related_name='result')
    performed_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True, related_name='lab_results_performed')
    reviewed_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True, related_name='lab_results_reviewed')
    
    result_value = models.TextField()
    result_unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=200, blank=True)
    
    result_status = models.CharField(max_length=20, choices=[
        ('normal', 'Normal'),
        ('abnormal', 'Abnormal'),
        ('critical', 'Critical'),
        ('inconclusive', 'Inconclusive'),
    ], blank=True)
    
    notes = models.TextField(blank=True)
    
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    result_date = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Result for {self.lab_order_item.test_type.name}"
