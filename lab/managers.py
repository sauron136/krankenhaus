from django.db import models
from django.utils import timezone
from django.db.models import Q  # Added for search_tests

class LabOrderManager(models.Manager):
    def pending_orders(self):
        """Get pending lab orders"""
        return self.filter(status='ordered')
    
    def urgent_orders(self):
        """Get urgent lab orders"""
        return self.filter(priority__in=['urgent', 'stat'])
    
    def for_patient(self, patient):
        """Get lab orders for specific patient"""
        return self.filter(patient=patient).order_by('-order_date')
    
    def by_doctor(self, doctor):
        """Get lab orders by specific doctor"""
        return self.filter(ordered_by=doctor).order_by('-order_date')
    
    def completed_orders(self):
        """Get completed lab orders"""
        return self.filter(status='completed')
    
    def today_orders(self):
        """Get today's lab orders"""
        today = timezone.now().date()
        return self.filter(order_date__date=today)


class LabTestTypeManager(models.Manager):
    def active_tests(self):
        """Get active lab test types"""
        return self.filter(is_active=True)
    
    def by_category(self, category):
        """Get tests by category"""
        return self.filter(category=category, is_active=True)
    
    def by_sample_type(self, sample_type):
        """Get tests by sample type"""
        return self.filter(sample_type=sample_type, is_active=True)
    
    def search_tests(self, query):
        """Search test types"""
        return self.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(category__icontains=query),
            is_active=True
        )
