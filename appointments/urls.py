from django.urls import path
from . import views

urlpatterns = [
    # Reference data endpoints
    path('departments/', views.DepartmentListView.as_view(), name='department-list'),
    path('appointment-types/', views.AppointmentTypeListView.as_view(), name='appointment-type-list'),
    path('providers/', views.ProviderListView.as_view(), name='provider-list'),
    
    # Provider availability
    path('availability/', views.ProviderAvailabilityView.as_view(), name='provider-availability'),
    
    # Main appointment endpoints
    path('', views.AppointmentListView.as_view(), name='appointment-list'),
    path('<int:appointment_id>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),
    path('<int:appointment_id>/status/', views.AppointmentStatusUpdateView.as_view(), name='appointment-status-update'),
    path('<int:appointment_id>/history/', views.AppointmentHistoryView.as_view(), name='appointment-history'),
    
    # Search and filtering
    path('search/', views.AppointmentSearchView.as_view(), name='appointment-search'),
    path('my-appointments/', views.MyAppointmentsView.as_view(), name='my-appointments'),
]
