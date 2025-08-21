from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def redirect_to_swagger(request):
    return redirect('/api/docs/')

# Configure schema view for drf-yasg
schema_view = get_schema_view(
    openapi.Info(
        title="Krankenhaus: A Hospital Management System",
        default_version='v1',
        description="API description",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="Your License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('', redirect_to_swagger),
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/medical_records/', include('medical_records.urls')),
    path('api/lab/', include('lab.urls')),
    path('api/schema/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
