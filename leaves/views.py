import logging

from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from rest_framework import generics, status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Leave, LeavePolicy
from .serializers import (
    LeaveSerializer,
    RegistrationSerializer,
    UpdatePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmployeeLoginSerializer,
    LeavePolicySerializer,
    InitializeSerializer,
    EmployeeListSerializer,
)

logger = logging.getLogger(__name__)

Employee = get_user_model()


class IsAdminOrHR(permissions.BasePermission):
    """
    Custom permission to only allow HR or Managers to edit leave policies.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.employee_role in ["HR", "MANAGER"]
        )


class LeavePolicyListView(generics.ListAPIView):
    """GET /leave-policies/ — List all leave policies (all authenticated users)."""

    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAuthenticated]


class LeavePolicyRetrieveView(generics.RetrieveAPIView):
    """GET /leave-policies/<pk>/ — Retrieve a single leave policy (all authenticated users)."""

    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAuthenticated]


class LeavePolicyCreateView(generics.CreateAPIView):
    """POST /leave-policies/create/ — Create a new leave policy (HR/Managers only)."""

    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        logger.info(
            "Leave policy created by user id=%s role=%s",
            request.user.id,
            request.user.employee_role,
        )
        return Response(
            {"status": 1, "message": "Leave policy created successfully"},
            status=status.HTTP_201_CREATED,
        )


class LeavePolicyUpdateView(generics.UpdateAPIView):
    """PATCH /leave-policies/<pk>/update/ — Update a leave policy (HR/Managers only)."""

    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        logger.info(
            "Leave policy id=%s updated by user id=%s",
            kwargs.get("pk"),
            request.user.id,
        )
        return Response(
            {"status": 1, "message": "Leave policy updated successfully"},
            status=status.HTTP_200_OK,
        )


class LeavePolicyDeleteView(generics.DestroyAPIView):
    """DELETE /leave-policies/<pk>/delete/ — Delete a leave policy (HR/Managers only)."""

    queryset = LeavePolicy.objects.all()
    serializer_class = LeavePolicySerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        logger.info(
            "Leave policy id=%s deleted by user id=%s",
            kwargs.get("pk"),
            request.user.id,
        )
        return Response(
            {"status": 1, "message": "Leave policy deleted successfully"},
            status=status.HTTP_200_OK,
        )



class InitializeView(generics.GenericAPIView):
    """
    View to initialize the system by creating a superuser on the first run if the database is empty.
    """

    serializer_class = InitializeSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Return information about the initialization endpoint."""
        if Employee.objects.exists():
            return Response(
                {
                    "status": 0,
                    "message": "System already initialized. Database is not empty.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "status": 1,
                "message": "System initialization endpoint. Send a POST request to initialize.",
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        """Initialize the system with a superuser if database is empty."""

        if Employee.objects.exists():
            logger.warning(
                "Initialization attempted but database already has employees"
            )
            return Response(
                {
                    "status": 0,
                    "message": "System already initialized. Database is not empty.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            superuser = Employee.objects.create_superuser(
                email="admin@company.com",
                username="admin",
                password="admin",
                first_name="admin",
                last_name="admin",
                employee_department="hr",
                employee_position="HR Administrator",
                phone_number="",
                employee_role="MANAGER",
            )

            logger.info(
                "Superuser created successfully id=%s email=%s role=%s",
                superuser.id,
                superuser.email,
                superuser.employee_role,
            )

            return Response(
                {
                    "status": 1,
                    "message": "System initialized successfully. Superuser created.",
                    "superuser": {
                        "email": superuser.email,
                        "role": superuser.employee_role,
                        "department": superuser.employee_department,
                        "name": f"{superuser.first_name} {superuser.last_name}",
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error("Error creating superuser during initialization: %s", str(e))
            return Response(
                {"status": 0, "message": f"Error initializing system: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that returns access token, refresh token, and user data.
    """

    def post(self, request, *args, **kwargs):
        """Override post to provide clear, specific error messages on login failure."""
        email = request.data.get("email", "").strip()
        password = request.data.get("password", "")
        response = None

        try:
            user = Employee.objects.get(email=email)
        except Employee.DoesNotExist:
            logger.warning("Login failed: no account found for email=%s", email)
            response = Response(
                {
                    "status": 0,
                    "message": f"No account found for email {email}.",
                    "code": "email_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )
            return response

        if not user.is_active:
            logger.warning("Login failed: account is inactive for email=%s", email)
            return Response(
                {
                    "status": 0,
                    "message": "Your account has been deactivated. Please contact HR.",
                    "code": "account_inactive",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.check_password(password):
            logger.warning("Login failed: incorrect password for email=%s", email)
            return Response(
                {
                    "status": 0,
                    "message": "Incorrect password. Please try again.",
                    "code": "wrong_password",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            user_serializer = EmployeeLoginSerializer(user)
            response.data["user"] = user_serializer.data
            response.data["status"] = 1
            response.data["message"] = "Login successful"
            logger.info(
                "User id=%s email=%s logged in successfully",
                user.id,
                user.email,
            )

        return response


class LeaveListCreateView(generics.ListCreateAPIView):
    """
    View to list all leave requests for the authenticated user and to create new leave requests.
    """

    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.employee_role in ["HR", "MANAGER"]:
            logger.info(
                "User id=%s role=%s requested all leave records",
                user.id,
                user.employee_role,
            )
            # Added "leave_type" to select_related to optimize ForeignKey lookup
            return Leave.objects.select_related("employee", "leave_type").all()

        queryset = Leave.objects.select_related("employee", "leave_type").filter(
            employee=user
        )
        logger.info(
            "User id=%s role=%s requested own leave records count=%s",
            user.id,
            user.employee_role,
            queryset.count(),
        )
        return queryset

    def perform_create(self, serializer):
        leave = serializer.save(employee=self.request.user)
        logger.info(
            "Leave created id=%s for user id=%s type=%s start=%s end=%s",
            leave.id,
            self.request.user.id,
            leave.leave_type.name,
            leave.start_date,
            leave.end_date,
        )

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response(
            {"status": 1, "message": "Leave applied successfully"},
            status=status.HTTP_201_CREATED,
        )


class PendingLeaveListView(generics.ListAPIView):
    """
    View to list all pending leave requests.
    """

    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.employee_role in ["HR", "MANAGER"]:
            logger.info(
                "User id=%s role=%s requested all pending leave records",
                user.id,
                user.employee_role,
            )
            return Leave.objects.select_related("employee", "leave_type").filter(
                status="PENDING"
            )

        queryset = Leave.objects.select_related("employee", "leave_type").filter(
            employee=user, status="PENDING"
        )
        logger.info(
            "User id=%s role=%s requested own pending leave records count=%s",
            user.id,
            user.employee_role,
            queryset.count(),
        )
        return queryset


class LeaveDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View to retrieve, update, or delete a specific leave request.
    """

    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.employee_role in ["HR", "MANAGER"]:
            logger.info(
                "User id=%s role=%s requested detail list of all leaves",
                user.id,
                user.employee_role,
            )
            return Leave.objects.select_related("employee", "leave_type").all()

        queryset = Leave.objects.select_related("employee", "leave_type").filter(
            employee=user
        )
        logger.info(
            "User id=%s role=%s requested detail list of own leaves count=%s",
            user.id,
            user.employee_role,
            queryset.count(),
        )
        return queryset

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            {"status": 1, "message": "Leave updated successfully"},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"status": 1, "message": "Leave deleted successfully"},
            status=status.HTTP_200_OK,
        )


class EmployeeView(generics.CreateAPIView):
    """View to handle employee creation (registration)."""

    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]
    queryset = Employee.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
        except Exception as e:
            logger.error(
                "Employee creation failed for email=%s: %s",
                request.data.get("email"),
                str(e),
            )
            return Response(
                {"status": 0, "message": "Employee creation failed", "data": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "Employee created successfully for email=%s", request.data.get("email")
        )

        return Response(
            {
                "status": 1,
                "message": "Employee created successfully",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class EmployeeListView(generics.ListAPIView):
    """
    View to list all employees with their complete information.
    Accessible to HR/Managers only.
    """

    serializer_class = EmployeeListSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    queryset = Employee.objects.all()

    def get(self, request, *args, **kwargs):
        """Override GET to add logging."""
        user = request.user
        logger.info(
            "User id=%s role=%s requested employee list",
            user.id,
            user.employee_role,
        )
        return super().get(request, *args, **kwargs)


class EmployeeDetailView(generics.RetrieveDestroyAPIView):
    """
    View to retrieve or delete a specific employee.
    Accessible to HR/Managers only.
    """

    serializer_class = EmployeeListSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    queryset = Employee.objects.all()

    def destroy(self, request, *args, **kwargs):
        """Override destroy to add logging and custom response."""
        employee = self.get_object()
        employee_email = employee.email
        employee_id = employee.id

        logger.info(
            "User id=%s (HR/Manager) is deleting employee id=%s email=%s",
            request.user.id,
            employee_id,
            employee_email,
        )

        try:
            super().destroy(request, *args, **kwargs)
            logger.info(
                "Employee id=%s email=%s deleted successfully by user id=%s",
                employee_id,
                employee_email,
                request.user.id,
            )
            return Response(
                {
                    "status": 1,
                    "message": f"Employee {employee_email} deleted successfully",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(
                "Failed to delete employee id=%s: %s",
                employee_id,
                str(e),
            )
            return Response(
                {"status": 0, "message": f"Failed to delete employee: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetRequestView(generics.GenericAPIView):
    """Send a password reset link to the user's email address."""

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        redirect_url = serializer.validated_data.get(
            "redirect_url", "http://localhost:3000/reset-password"
        )
        user_model = get_user_model()

        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            logger.warning("Password reset requested for non-existent email=%s", email)
            return Response(
                {
                    "detail": "If an account with this email exists, a reset link has been sent."
                },
                status=status.HTTP_200_OK,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        if "?" in redirect_url:
            reset_url = f"{redirect_url}&uid={uid}&token={token}"
        else:
            reset_url = f"{redirect_url}?uid={uid}&token={token}"

        subject = "Password Reset Request"
        message = (
            "Hello,\n\n"
            "You requested a password reset for your account. "
            "Click the link below to set a new password:\n\n"
            f"{reset_url}\n\n"
            "If you did not request this, you can safely ignore this email."
        )

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
        send_mail(subject, message, from_email, [email])

        logger.info("Password reset email sent to email=%s uid=%s", email, uid)

        return Response(
            {"status": 1, "message": "Password reset link sent successfully"},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset using uid and token, then update the password."""

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uidb64 = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        user_model = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = user_model.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
            logger.warning("Invalid password reset UID=%s", uidb64)
            return Response(
                {"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            logger.warning(
                "Invalid/expired password reset token for user id=%s", user.id
            )
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        logger.info(
            "Password reset successfully via email link for user id=%s", user.id
        )

        return Response(
            {"status": 1, "message": "Password reset successfully"},
            status=status.HTTP_200_OK,
        )


class UpdatePasswordView(generics.GenericAPIView):
    """
    View to handle password updates for authenticated users.
    """

    serializer_class = UpdatePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def _update_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.get_object()
        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        logger.info("Password update attempt for user id=%s", user.id)

        if not user.check_password(old_password):
            logger.warning(
                "Password update failed for user id=%s: wrong password", user.id
            )
            return Response(
                {"old_password": ["Wrong password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        logger.info("Password updated successfully for user id=%s", user.id)

        return Response(
            {"status": 1, "message": "Password updated successfully"},
            status=status.HTTP_200_OK,
        )

    def put(self, request, *args, **kwargs):
        return self._update_password(request)

    def post(self, request, *args, **kwargs):
        return self._update_password(request)


class LeavesSummaryDashboardView(generics.GenericAPIView):
    """
    Dashboard view for HR/Managers only.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.employee_role not in ["HR", "MANAGER"]:
            logger.warning(
                "User id=%s role=%s attempted to access leaves summary without permission",
                user.id,
                user.employee_role,
            )
            return Response(
                {
                    "status": 0,
                    "message": "You don't have permission to access this dashboard. Only HR and Managers can view this.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        all_leaves = Leave.objects.all()

        total_leaves = all_leaves.count()
        total_approved = all_leaves.filter(status="APPROVED").count()
        total_rejected = all_leaves.filter(status="REJECTED").count()
        total_pending = all_leaves.filter(status="PENDING").count()

        all_employees = Employee.objects.annotate(
            total_applications=Count("leaves"),
            approved_applications=Count("leaves", filter=Q(leaves__status="APPROVED")),
            rejected_applications=Count("leaves", filter=Q(leaves__status="REJECTED")),
            pending_applications=Count("leaves", filter=Q(leaves__status="PENDING")),
        )

        user_breakdown = []
        for employee in all_employees:
            emp_data = {
                "user_id": employee.id,
                "email": employee.email,
                "full_name": f"{employee.first_name} {employee.last_name}".strip(),
                "role": employee.employee_role,
                "department": employee.employee_department,
                "position": employee.employee_position,
                "applications": {
                    "total": employee.total_applications,
                    "approved": employee.approved_applications,
                    "rejected": employee.rejected_applications,
                    "pending": employee.pending_applications,
                },
            }
            user_breakdown.append(emp_data)

        logger.info(
            "User id=%s (HR/Manager) accessed leaves summary dashboard. Total leaves: %s (Approved: %s, Rejected: %s, Pending: %s)",
            user.id,
            total_leaves,
            total_approved,
            total_rejected,
            total_pending,
        )

        return Response(
            {
                "status": 1,
                "message": "Leaves summary dashboard retrieved successfully",
                "summary": {
                    "total_applications": total_leaves,
                    "approved_applications": total_approved,
                    "rejected_applications": total_rejected,
                    "pending_applications": total_pending,
                },
                "users": user_breakdown,
            },
            status=status.HTTP_200_OK,
        )
