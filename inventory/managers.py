from django.db import models
from django.utils import timezone
from django.db.models import Q, F, Sum  # Added F and Sum for low_stock_items and out_of_stock_items

class InventoryItemManager(models.Manager):
    def active_items(self):
        """Get active inventory items"""
        return self.filter(is_active=True)
    
    def low_stock_items(self):
        """Get items below reorder level"""
        return self.filter(
            is_active=True
        ).annotate(
            current_stock=Sum('stock_levels__quantity', filter=Q(stock_levels__is_active=True))
        ).filter(
            current_stock__lt=F('reorder_level')
        )
    
    def out_of_stock_items(self):
        """Get out of stock items"""
        return self.filter(
            is_active=True
        ).annotate(
            current_stock=Sum('stock_levels__quantity', filter=Q(stock_levels__is_active=True))
        ).filter(
            Q(current_stock=0) | Q(current_stock__isnull=True)
        )
    
    def expiring_soon(self, days=30):
        """Get items expiring within specified days"""
        cutoff_date = timezone.now().date() + timezone.timedelta(days=days)
        return self.filter(
            stock_levels__expiry_date__lte=cutoff_date,
            stock_levels__expiry_date__gte=timezone.now().date(),
            stock_levels__is_active=True,
            is_active=True
        ).distinct()
    
    def by_category(self, category):
        """Get items by category"""
        return self.filter(category=category, is_active=True)
    
    def search_items(self, query):
        """Get inventory items"""
        return self.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query),
            is_active=True
        )
