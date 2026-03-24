from django.urls import path
from .views import (
    LeaveDetailView,
    LeaveListCreateView,
    PendingLeaveListView,
    EmployeeView,
    UpdatePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    InitializeView,
    CustomTokenObtainPairView,
    LeavesSummaryDashboardView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    # Initialization endpoint
    path("init/", InitializeView.as_view(), name="initialize"),
    # admin actions on leaves
    path("leaves/update/<int:pk>/", LeaveDetailView.as_view(), name="update-leave"),
    # Leave endpoints
    path("leaves/history/", LeaveListCreateView.as_view(), name="leave-list"),
    path("leaves/<int:pk>/", LeaveDetailView.as_view(), name="leave-detail"),
    path("leaves/apply/", LeaveListCreateView.as_view(), name="apply-leave"),
    path("leaves/pending/", PendingLeaveListView.as_view(), name="pending-leaves"),
    path("leaves/all/", LeaveListCreateView.as_view(), name="all-leaves"),
    # Employee actions
    path("employees/create/", EmployeeView.as_view(), name="create-employee"),
    path(
        "employees/update/password/",
        UpdatePasswordView.as_view(),
        name="update-password",
    ),
    path("leaves/statistics/", LeavesSummaryDashboardView.as_view(), name="leave-statistics"),
    path(
        "leaves/summary/",
        LeavesSummaryDashboardView.as_view(),
        name="leaves-summary-dashboard",
    ),
    path(
        "auth/password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path(
        "auth/password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    # JWT views for login and token refresh
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
