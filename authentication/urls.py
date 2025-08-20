from django.urls import path
from .views import (
    PersonnelLoginView,
    PatientLoginView,
    PersonnelRegisterView,
    PatientRegisterView,
    VerifyEmailView,
    ResendOTPView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
    TokenRefreshView,
    ValidateTokenView,
    LogoutView
)

app_name = 'authentication'

urlpatterns = [
    # Login/Logout
    path('personnel/login/', PersonnelLoginView.as_view(), name='personnel-login'),
    path('patient/login/', PatientLoginView.as_view(), name='patient-login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Registration & Email Verification
    path('personnel/register/', PersonnelRegisterView.as_view(), name='personnel-register'),
    path('patient/register/', PatientRegisterView.as_view(), name='patient-register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    
    # OTP Management
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # Password Management
    path('password/reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('password/change/', ChangePasswordView.as_view(), name='change-password'),
    
    # Token Management
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/validate/', ValidateTokenView.as_view(), name='validate-token'),
]
