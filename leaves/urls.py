from django.urls import path
from .views import (
    LeaveDetailView, 
    LeaveListCreateView,
    RegistrationView,
    UpdatePasswordView
    )
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)   

urlpatterns = [
    # Leave endpoints
    path('leaves/', LeaveListCreateView.as_view(), name='leave-list'),
    path('leaves/<int:pk>/', LeaveDetailView.as_view(), name='leave-detail'),

    # Authentication endpoints
    path('auth/register/', RegistrationView.as_view(), name='register'),
    path('auth/update-password/', UpdatePasswordView.as_view(), name='update-password'),

    # JWT views for login and token refresh
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
