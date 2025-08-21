from django.db import models

from .managers import InventoryItemManager  # Import the manager

class InventoryCategory(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Inventory Categories"

class InventoryItem(models.Model):
    objects = InventoryItemManager()  # Assign the custom manager

    name = models.CharField(max_length=200)
    category = models.ForeignKey(InventoryCategory, on_delete=models.SET_NULL, null=True, related_name='items')
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    unit_of_measure = models.CharField(max_length=50)
    reorder_level = models.IntegerField(default=10)
    maximum_stock_level = models.IntegerField(null=True, blank=True)
    
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def current_stock(self):
        return sum(stock.quantity for stock in self.stock_levels.filter(is_active=True))
    
    def __str__(self):
        return f"{self.name} ({self.sku})"

class StockLevel(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='stock_levels')
    quantity = models.IntegerField()
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey('accounts.Personnel', on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.item.name} - {self.quantity} units"
