from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    LOCATION_TYPES = [
        ('WARD', 'Ward'),
        ('STORAGE', 'Storage Room'),
        ('PHARMACY', 'Pharmacy'),
        ('OR', 'Operating Room'),
        ('ICU', 'ICU'),
        ('ER', 'Emergency Room'),
        ('LAB', 'Laboratory'),
        ('MAINTENANCE', 'Maintenance'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    floor = models.CharField(max_length=10, blank=True)
    room_number = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"


class Item(models.Model):
    CATEGORY_CHOICES = [
        ('MEDICAL_SUPPLY', 'Medical Supply'),
        ('PHARMACEUTICAL', 'Pharmaceutical'),
        ('EQUIPMENT', 'Equipment'),
        ('STERILE_SUPPLY', 'Sterile Supply'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('DISCONTINUED', 'Discontinued'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    reorder_level = models.IntegerField(validators=[MinValueValidator(0)])
    reorder_quantity = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.sku})"


class Stock(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock_records')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['item', 'location', 'lot_number']
    
    def __str__(self):
        return f"{self.item.name} at {self.location.name}: {self.quantity}"
    
    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
    
    @property
    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days


class MedicalSupply(Item):
    SUPPLY_TYPES = [
        ('DISPOSABLE', 'Disposable'),
        ('REUSABLE', 'Reusable'),
        ('IMPLANT', 'Implant'),
    ]
    
    supply_type = models.CharField(max_length=20, choices=SUPPLY_TYPES)
    is_sterile = models.BooleanField(default=False)
    latex_free = models.BooleanField(default=True)
    size = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = "Medical Supply"
        verbose_name_plural = "Medical Supplies"


class Pharmaceutical(Item):
    DOSAGE_FORMS = [
        ('TABLET', 'Tablet'),
        ('CAPSULE', 'Capsule'),
        ('LIQUID', 'Liquid'),
        ('INJECTION', 'Injection'),
        ('CREAM', 'Cream'),
        ('OINTMENT', 'Ointment'),
        ('INHALER', 'Inhaler'),
        ('DROPS', 'Drops'),
    ]
    
    CONTROLLED_SCHEDULES = [
        ('', 'Not Controlled'),
        ('I', 'Schedule I'),
        ('II', 'Schedule II'),
        ('III', 'Schedule III'),
        ('IV', 'Schedule IV'),
        ('V', 'Schedule V'),
    ]
    
    generic_name = models.CharField(max_length=255, blank=True)
    brand_name = models.CharField(max_length=255, blank=True)
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORMS)
    strength = models.CharField(max_length=100)
    controlled_schedule = models.CharField(max_length=5, choices=CONTROLLED_SCHEDULES, blank=True)
    requires_prescription = models.BooleanField(default=True)
    storage_temperature = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Pharmaceutical"
        verbose_name_plural = "Pharmaceuticals"


class Equipment(Item):
    EQUIPMENT_TYPES = [
        ('DIAGNOSTIC', 'Diagnostic Equipment'),
        ('THERAPEUTIC', 'Therapeutic Equipment'),
        ('SURGICAL', 'Surgical Equipment'),
        ('MONITORING', 'Monitoring Equipment'),
        ('MOBILITY', 'Mobility Equipment'),
        ('FURNITURE', 'Medical Furniture'),
    ]
    
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPES)
    model_number = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    manufacture_date = models.DateField(blank=True, null=True)
    warranty_expiry = models.DateField(blank=True, null=True)
    maintenance_interval_days = models.IntegerField(blank=True, null=True)
    last_maintenance = models.DateField(blank=True, null=True)
    is_portable = models.BooleanField(default=True)
    power_requirements = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Equipment"
        verbose_name_plural = "Equipment"
    
    @property
    def needs_maintenance(self):
        if not self.maintenance_interval_days or not self.last_maintenance:
            return False
        from django.utils import timezone
        next_maintenance = self.last_maintenance + timezone.timedelta(days=self.maintenance_interval_days)
        return next_maintenance <= timezone.now().date()


class SterileSupply(Item):
    STERILIZATION_METHODS = [
        ('AUTOCLAVE', 'Autoclave'),
        ('ETO', 'Ethylene Oxide'),
        ('RADIATION', 'Gamma Radiation'),
        ('PLASMA', 'Hydrogen Peroxide Plasma'),
    ]
    
    sterilization_method = models.CharField(max_length=20, choices=STERILIZATION_METHODS)
    sterile_until = models.DateField()
    package_integrity = models.BooleanField(default=True)
    resterilizable = models.BooleanField(default=False)
    sterilization_cycles = models.IntegerField(default=0)
    max_sterilization_cycles = models.IntegerField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Sterile Supply"
        verbose_name_plural = "Sterile Supplies"
    
    @property
    def is_sterile(self):
        if not self.package_integrity:
            return False
        from django.utils import timezone
        return self.sterile_until >= timezone.now().date()


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('TRANSFER', 'Transfer'),
        ('ADJUSTMENT', 'Adjustment'),
        ('EXPIRED', 'Expired'),
        ('DAMAGED', 'Damaged'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.item.name} ({self.quantity})"
