from django.urls import path
from authentication.api import views
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('', views.getRoutes, name='routes'),
    path('login/', views.LoginView.as_view(), name='custom_auth_token'),
    path('validate-token/', views.ValidateToken.as_view(), name='validate_token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('send-otp/', views.SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('update-user/', views.UpdateUserView.as_view(), name='update-user'),
    path('get-user/', views.GetUserView.as_view(), name='get-user'),
]
