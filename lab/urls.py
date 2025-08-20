from django.urls import path
from . import views

urlpatterns = [
    # Test catalog
    path('categories/', views.TestCategoryListView.as_view(), name='test-category-list'),
    path('tests/', views.LabTestListView.as_view(), name='lab-test-list'),
    path('tests/<int:test_id>/', views.LabTestDetailView.as_view(), name='lab-test-detail'),
    
    # Lab orders
    path('orders/', views.LabOrderListView.as_view(), name='lab-order-list'),
    path('orders/<int:order_id>/', views.LabOrderDetailView.as_view(), name='lab-order-detail'),
    path('orders/pending/', views.PendingOrdersView.as_view(), name='pending-orders'),
    
    # Sample management
    path('samples/', views.SampleListView.as_view(), name='sample-list'),
    path('samples/<int:sample_id>/', views.SampleDetailView.as_view(), name='sample-detail'),
    
    # Results management
    path('results/', views.LabResultListView.as_view(), name='lab-result-list'),
    path('results/<int:result_id>/', views.LabResultDetailView.as_view(), name='lab-result-detail'),
    
    # Critical values
    path('critical-values/', views.CriticalValuesView.as_view(), name='critical-values'),
    path('critical-values/<int:critical_id>/', views.CriticalValueDetailView.as_view(), name='critical-value-detail'),
]
