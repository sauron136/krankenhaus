from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from .models import (
    Supplier, Location, Item, Stock, MedicalSupply, 
    Pharmaceutical, Equipment, SterileSupply, StockTransaction
)

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class SupplierBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'phone', 'email']

class LocationSerializer(serializers.ModelSerializer):
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    
    class Meta:
        model = Location
        fields = '__all__'

class LocationBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'location_type', 'floor', 'room_number']

class ItemListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    total_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = [
            'id', 'name', 'sku', 'category', 'category_display',
            'supplier_name', 'unit_cost', 'reorder_level', 
            'total_stock', 'status'
        ]
    
    def get_total_stock(self, obj):
        return obj.stock_records.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

class ItemDetailSerializer(serializers.ModelSerializer):
    supplier = SupplierBasicSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    stock_locations = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = '__all__'
    
    def get_stock_locations(self, obj):
        stocks = obj.stock_records.filter(quantity__gt=0)
        return StockListSerializer(stocks, many=True).data

class ItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        exclude = ['created_at', 'updated_at']
    
    def validate_unit_cost(self, value):
        if value <= 0:
            raise serializers.ValidationError("Unit cost must be greater than 0")
        return value
    
    def validate_reorder_level(self, value):
        if value < 0:
            raise serializers.ValidationError("Reorder level cannot be negative")
        return value

class StockListSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id', 'item_name', 'location_name', 'quantity', 
            'lot_number', 'expiry_date', 'is_expired', 
            'days_until_expiry', 'last_updated'
        ]

class StockDetailSerializer(serializers.ModelSerializer):
    item = ItemListSerializer(read_only=True)
    location = LocationBasicSerializer(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Stock
        fields = '__all__'

class StockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        exclude = ['last_updated']
    
    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value
    
    def validate_expiry_date(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Expiry date cannot be in the past")
        return value

class MedicalSupplySerializer(serializers.ModelSerializer):
    supplier = SupplierBasicSerializer(read_only=True)
    supply_type_display = serializers.CharField(source='get_supply_type_display', read_only=True)
    total_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalSupply
        fields = '__all__'
    
    def get_total_stock(self, obj):
        return obj.stock_records.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

class MedicalSupplyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalSupply
        exclude = ['created_at', 'updated_at']

class PharmaceuticalSerializer(serializers.ModelSerializer):
    supplier = SupplierBasicSerializer(read_only=True)
    dosage_form_display = serializers.CharField(source='get_dosage_form_display', read_only=True)
    controlled_schedule_display = serializers.CharField(source='get_controlled_schedule_display', read_only=True)
    total_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Pharmaceutical
        fields = '__all__'
    
    def get_total_stock(self, obj):
        return obj.stock_records.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

class PharmaceuticalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmaceutical
        exclude = ['created_at', 'updated_at']
    
    def validate_strength(self, value):
        if not value.strip():
            raise serializers.ValidationError("Strength cannot be empty")
        return value

class EquipmentSerializer(serializers.ModelSerializer):
    supplier = SupplierBasicSerializer(read_only=True)
    equipment_type_display = serializers.CharField(source='get_equipment_type_display', read_only=True)
    needs_maintenance = serializers.BooleanField(read_only=True)
    total_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Equipment
        fields = '__all__'
    
    def get_total_stock(self, obj):
        return obj.stock_records.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

class EquipmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        exclude = ['created_at', 'updated_at']
    
    def validate_manufacture_date(self, value):
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Manufacture date cannot be in the future")
        return value

class SterileSupplySerializer(serializers.ModelSerializer):
    supplier = SupplierBasicSerializer(read_only=True)
    sterilization_method_display = serializers.CharField(source='get_sterilization_method_display', read_only=True)
    is_sterile = serializers.BooleanField(read_only=True)
    total_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = SterileSupply
        fields = '__all__'
    
    def get_total_stock(self, obj):
        return obj.stock_records.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

class SterileSupplyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SterileSupply
        exclude = ['created_at', 'updated_at']
    
    def validate_sterile_until(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Sterile until date cannot be in the past")
        return value
    
    def validate_max_sterilization_cycles(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Max sterilization cycles must be greater than 0")
        return value

class StockTransactionSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    total_value = serializers.SerializerMethodField()
    
    class Meta:
        model = StockTransaction
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_total_value(self, obj):
        if obj.unit_cost:
            return abs(obj.quantity) * obj.unit_cost
        return None

class StockTransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTransaction
        exclude = ['created_at']
    
    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity cannot be zero")
        return value

class LowStockReportSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    sku = serializers.CharField()
    current_stock = serializers.IntegerField()
    reorder_level = serializers.IntegerField()
    reorder_quantity = serializers.IntegerField()
    supplier_name = serializers.CharField()
    category = serializers.CharField()

class ExpiringItemsReportSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    item_name = serializers.CharField()
    location_name = serializers.CharField()
    quantity = serializers.IntegerField()
    expiry_date = serializers.DateField()
    days_until_expiry = serializers.IntegerField()
    lot_number = serializers.CharField()

class InventoryValueReportSerializer(serializers.Serializer):
    category = serializers.CharField()
    total_items = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
