from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Suppliers
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    
    # Locations
    path('locations/', views.LocationListCreateView.as_view(), name='location-list-create'),
    path('locations/<int:pk>/', views.LocationDetailView.as_view(), name='location-detail'),
    
    # Items (base items)
    path('items/', views.ItemListCreateView.as_view(), name='item-list-create'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),
    
    # Stock management
    path('stock/', views.StockListCreateView.as_view(), name='stock-list-create'),
    path('stock/<int:pk>/', views.StockDetailView.as_view(), name='stock-detail'),
    
    # Specialized item types
    path('medical-supplies/', views.MedicalSupplyListCreateView.as_view(), name='medical-supply-list-create'),
    path('pharmaceuticals/', views.PharmaceuticalListCreateView.as_view(), name='pharmaceutical-list-create'),
    path('equipment/', views.EquipmentListCreateView.as_view(), name='equipment-list-create'),
    path('sterile-supplies/', views.SterileSupplyListCreateView.as_view(), name='sterile-supply-list-create'),
    
    # Transactions
    path('transactions/', views.StockTransactionListView.as_view(), name='transaction-list'),
    
    # Reports
    path('reports/low-stock/', views.LowStockReportView.as_view(), name='low-stock-report'),
    path('reports/expiring/', views.ExpiringItemsReportView.as_view(), name='expiring-items-report'),
    path('reports/inventory-value/', views.InventoryValueReportView.as_view(), name='inventory-value-report'),
]
