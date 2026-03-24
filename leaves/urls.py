from django.urls import path
from .views import (
    LeaveDetailView,
    LeaveListCreateView,
    PendingLeaveListView,
    EmployeeView,
    EmployeeListView,
    EmployeeDetailView,
    UpdatePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    InitializeView,
    CustomTokenObtainPairView,
    LeavesSummaryDashboardView,
    LeavePolicyListView,
    LeavePolicyRetrieveView,
    LeavePolicyCreateView,
    LeavePolicyUpdateView,
    LeavePolicyDeleteView,
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

urlpatterns = [
    # Initialization endpoint
    path("init/", InitializeView.as_view(), name="initialize"),
    # Leave Policy endpoints
    path("leave-policies/", LeavePolicyListView.as_view(), name="policy-list"),
    path("leave-policies/<int:pk>/", LeavePolicyRetrieveView.as_view(), name="policy-detail"),
    path("leave-policies/create/", LeavePolicyCreateView.as_view(), name="policy-create"),
    path("leave-policies/<int:pk>/update/", LeavePolicyUpdateView.as_view(), name="policy-update"),
    path("leave-policies/<int:pk>/delete/", LeavePolicyDeleteView.as_view(), name="policy-delete"),
    # admin actions on leaves
    path("leaves/update/<int:pk>/", LeaveDetailView.as_view(), name="update-leave"),
    # Leave endpoints
    path("leaves/history/", LeaveListCreateView.as_view(), name="leave-list"),
    path("leaves/<int:pk>/", LeaveDetailView.as_view(), name="leave-detail"),
    path("leaves/apply/", LeaveListCreateView.as_view(), name="apply-leave"),
    path("leaves/pending/", PendingLeaveListView.as_view(), name="pending-leaves"),
    path("leaves/all/", LeaveListCreateView.as_view(), name="all-leaves"),
    path("leaves/statistics/", LeavesSummaryDashboardView.as_view(), name="leave-statistics"),
    path(
        "leaves/summary/",
        LeavesSummaryDashboardView.as_view(),
        name="leaves-summary-dashboard",
    ),
    # Employee endpoints
    path("employee/create/", EmployeeView.as_view(), name="create-employee"),
    path("employees/", EmployeeListView.as_view(), name="employee-list"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path(
        "employees/update/password/",
        UpdatePasswordView.as_view(),
        name="update-password",
    ),
    # Auth endpoints
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
