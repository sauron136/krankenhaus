from django.db import models
from django.utils import timezone
from appointments.models import Appointment

class TestCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Test Categories"

class LabTest(models.Model):
    SPECIMEN_TYPES = [
        ('blood', 'Blood'),
        ('serum', 'Serum'),
        ('plasma', 'Plasma'),
        ('urine', 'Urine'),
        ('stool', 'Stool'),
        ('sputum', 'Sputum'),
        ('csf', 'Cerebrospinal Fluid'),
        ('tissue', 'Tissue'),
        ('swab', 'Swab'),
        ('saliva', 'Saliva'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name='tests')
    specimen_type = models.CharField(max_length=20, choices=SPECIMEN_TYPES)
    specimen_volume = models.CharField(max_length=50, blank=True)  # e.g., "5ml", "10-15ml"
    
    normal_range_male = models.TextField(blank=True)
    normal_range_female = models.TextField(blank=True)
    normal_range_pediatric = models.TextField(blank=True)
    
    turnaround_time_hours = models.IntegerField(default=24)  # Expected completion time
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    preparation_instructions = models.TextField(blank=True)  # e.g., "Fasting required"
    methodology = models.CharField(max_length=200, blank=True)  # Testing method
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        ordering = ['category__name', 'name']

class LabOrder(models.Model):
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT'),
        ('timed', 'Timed'),
    ]
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='lab_orders')
    patient = models.ForeignKey('accounts.Patient', on_delete=models.CASCADE, related_name='lab_orders')
    ordered_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='lab_orders_created')
    
    order_date = models.DateTimeField(default=timezone.now)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='routine')
    clinical_indication = models.TextField(blank=True)  # Why these tests are needed
    
    special_instructions = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Lab Order for {self.patient} - {self.order_date.date()}"
    
    class Meta:
        ordering = ['-order_date']

class LabOrderItem(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('sample_pending', 'Sample Collection Pending'),
        ('sample_collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]
    
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='items')
    lab_test = models.ForeignKey(LabTest, on_delete=models.CASCADE, null=True, blank=True)
    
    # For dynamic tests not in our database
    test_name = models.CharField(max_length=200, blank=True)
    test_code = models.CharField(max_length=50, blank=True)
    specimen_type = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        test_name = self.lab_test.name if self.lab_test else self.test_name
        return f"{test_name} for {self.lab_order.patient}"
    
    def get_test_display(self):
        if self.lab_test:
            return f"{self.lab_test.name} ({self.lab_test.code})"
        else:
            return f"{self.test_name} ({self.test_code})"

class Sample(models.Model):
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]
    
    REJECTION_REASONS = [
        ('insufficient_volume', 'Insufficient Volume'),
        ('hemolyzed', 'Hemolyzed'),
        ('contaminated', 'Contaminated'),
        ('improper_collection', 'Improper Collection'),
        ('expired', 'Expired'),
        ('mislabeled', 'Mislabeled'),
        ('other', 'Other'),
    ]
    
    order_item = models.ForeignKey(LabOrderItem, on_delete=models.CASCADE, related_name='samples')
    sample_id = models.CharField(max_length=100, unique=True)  # Barcode/tracking number
    
    collected_at = models.DateTimeField()
    collected_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, related_name='samples_collected')
    collection_site = models.CharField(max_length=100, blank=True)  # e.g., "Left arm", "Midstream"
    
    received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, null=True, blank=True, related_name='samples_received')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    rejection_reason = models.CharField(max_length=50, choices=REJECTION_REASONS, blank=True)
    
    volume_collected = models.CharField(max_length=50, blank=True)
    container_type = models.CharField(max_length=100, blank=True)  # e.g., "EDTA tube", "Sterile container"
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Sample {self.sample_id} - {self.order_item.get_test_display()}"

class LabResult(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preliminary', 'Preliminary'),
        ('final', 'Final'),
        ('corrected', 'Corrected'),
        ('cancelled', 'Cancelled'),
    ]
    
    ABNORMAL_FLAGS = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('low', 'Low'),
        ('critical_high', 'Critical High'),
        ('critical_low', 'Critical Low'),
        ('abnormal', 'Abnormal'),
    ]
    
    order_item = models.ForeignKey(LabOrderItem, on_delete=models.CASCADE, related_name='results')
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE, null=True, blank=True, related_name='results')
    
    result_value = models.TextField()  # Can be numeric, text, or complex
    unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=200, blank=True)
    
    abnormal_flag = models.CharField(max_length=20, choices=ABNORMAL_FLAGS, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    performed_at = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, null=True, blank=True, related_name='lab_results_performed')
    
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, null=True, blank=True, related_name='lab_results_reviewed')
    
    interpretation = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Result for {self.order_item.get_test_display()} - {self.result_value}"
    
    class Meta:
        ordering = ['-created_at']

class CriticalValue(models.Model):
    """For tracking critical results that need immediate attention"""
    result = models.OneToOneField(LabResult, on_delete=models.CASCADE, related_name='critical_alert')
    notified_personnel = models.ManyToManyField('accounts.Personnel', related_name='critical_notifications', blank=True)
    
    notification_sent_at = models.DateTimeField(default=timezone.now)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey('accounts.Personnel', on_delete=models.CASCADE, null=True, blank=True, related_name='critical_alerts_acknowledged')
    
    action_taken = models.TextField(blank=True)
    
    def __str__(self):
        return f"Critical Alert: {self.result.order_item.get_test_display()} - {self.result.result_value}"
