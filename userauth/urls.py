from django.conf import settings
from django.conf.urls import url
from django.urls import path,include
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views
from . import views
router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    path('login/', views.MyTokenObtainPairView.as_view()),
    path('login/refresh/', jwt_views.TokenRefreshView.as_view()),
    path('verify/', views.OTPVerificationView.as_view()),
    path('password/reset/', views.PasswordResetView.as_view()),
    path('password/reset/verify/', views.PasswordResetOTPConfirmView.as_view()),
    path('otp/resend/', views.OTPResend.as_view()),
] 

