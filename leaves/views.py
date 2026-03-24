import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Leave
from .serializers import (
    LeaveSerializer,
    RegistrationSerializer,
    UpdatePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmployeeLoginSerializer,
    LeaveStatisticsSerializer,
)

logger = logging.getLogger(__name__)

Employee = get_user_model()


class InitializeView(generics.GenericAPIView):
    """
    View to initialize the system by creating a superuser on the first run if the database is empty.

    This endpoint checks if any employees exist in the database. If not, it creates a superuser
    with predefined credentials for initial system setup.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Initialize the system with a superuser if database is empty."""

        # Check if database is empty
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
            # Create superuser with specified credentials
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

    Returns:
        - access: JWT access token
        - refresh: JWT refresh token
        - user: Employee user data (id, email, name, role, department, etc.)
    """

    def post(self, request, *args, **kwargs):
        """Override post to include user data in the response."""
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            try:
                # Get the user from the email in the request
                email = request.data.get("email")
                user = Employee.objects.get(email=email)

                # Serialize user data
                user_serializer = EmployeeLoginSerializer(user)

                # Add user data to response
                response.data["user"] = user_serializer.data
                response.data["status"] = 1
                response.data["message"] = "Login successful"

                logger.info(
                    "User id=%s email=%s logged in successfully",
                    user.id,
                    user.email,
                )
            except Employee.DoesNotExist:
                logger.warning("Login attempted for non-existent email=%s", email)
                pass

        return response


class LeaveListCreateView(generics.ListCreateAPIView):
    """
    View to list all leave requests for the authenticated user and to create new leave requests.

    Args:
        generics (ListCreateAPIView): Provides GET and POST handlers for listing and creating leave requests.

    Returns:
        A list of leave requests for the authenticated user on GET request, and the created leave request on POST request.
    """

    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the leaves for the currently authenticated user."""
        user = self.request.user

        # HR and Manager can see all leave requests
        if user.employee_role in ["HR", "MANAGER"]:
            logger.info(
                "User id=%s role=%s requested all leave records",
                user.id,
                user.employee_role,
            )
            data = Leave.objects.all()
            print(f"All leave records: {data}")
            return data

        queryset = Leave.objects.filter(employee=self.request.user)
        logger.info(
            "User id=%s role=%s requested own leave records count=%s",
            user.id,
            user.employee_role,
            queryset.count(),
        )
        return queryset

    def perform_create(self, serializer):
        """Associate the new leave request with the currently authenticated user."""
        leave = serializer.save(employee=self.request.user)

        logger.info(
            "Leave created id=%s for user id=%s type=%s start=%s end=%s",
            leave.id,
            self.request.user.id,
            leave.leave_type,
            leave.start_date,
            leave.end_date,
        )

    def create(self, request, *args, **kwargs):
        """Override create to return custom JSON response."""
        super().create(request, *args, **kwargs)
        return Response(
            {"status": 1, "message": "Leave applied successfully"},
            status=status.HTTP_201_CREATED,
        )

    def get_exception_handler_context(self):
        """Add custom context for exception handling."""
        context = super().get_exception_handler_context()
        return context


class PendingLeaveListView(generics.ListAPIView):
    """
    View to list all pending leave requests.

    - HR and Manager can see all pending leave requests
    - Regular staff can see their own pending leave requests

    Returns:
        A list of pending leave requests filtered by user role and status.
    """

    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return pending leaves based on user role."""
        user = self.request.user

        # HR and Manager can see all pending leave requests
        if user.employee_role in ["HR", "MANAGER"]:
            logger.info(
                "User id=%s role=%s requested all pending leave records",
                user.id,
                user.employee_role,
            )
            return Leave.objects.filter(status="PENDING")

        # Regular staff can see only their own pending leave requests
        queryset = Leave.objects.filter(employee=self.request.user, status="PENDING")
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

    Args:
        generics (RetrieveUpdateDestroyAPIView): Provides GET, PUT, PATCH, and DELETE handlers for a specific leave request.

    Returns:
        The leave request details on GET request, the updated leave request on PUT/PATCH request,
        and a success message on DELETE request.
    """

    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return the leaves for the currently authenticated user."""
        user = self.request.user
        if user.employee_role in ["HR", "MANAGER"]:
            logger.info(
                "User id=%s role=%s requested detail list of all leaves",
                user.id,
                user.employee_role,
            )
            return Leave.objects.all()

        queryset = Leave.objects.filter(employee=self.request.user)
        logger.info(
            "User id=%s role=%s requested detail list of own leaves count=%s",
            user.id,
            user.employee_role,
            queryset.count(),
        )
        return queryset

    def update(self, request, *args, **kwargs):
        """Override update to return custom JSON response."""
        super().update(request, *args, **kwargs)
        return Response(
            {"status": 1, "message": "Leave updated successfully"},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        """Override destroy to return custom JSON response."""
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
        # Do not log the raw password; only log non-sensitive fields.
        logger.info(
            "Registration attempt for email=%s department=%s position=%s role=%s",
            request.data.get("email"),
            request.data.get("employee_department"),
            request.data.get("employee_position"),
            request.data.get("employee_role"),
        )
        # format the request
        employee_data = {
            "email": request.data.get("email"),
            "first_name": request.data.get("first_name"),
            "last_name": request.data.get("last_name"),
            "employee_department": request.data.get("department"),
            "employee_position": request.data.get("position"),
            "phone_number": request.data.get("phone_number"),
            "employee_role": request.data.get("role"),
        }

        super().create(employee_data, *args, **kwargs)
        logger.info(
            "Registration success for email=%s",
            request.data.get("email"),
        )
        return Response(
            {"status": 1, "message": "Employee created successfully"},
            status=status.HTTP_201_CREATED,
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
            # Do not reveal whether the email exists
            logger.warning("Password reset requested for non-existent email=%s", email)
            return Response(
                {
                    "detail": "If an account with this email exists, a reset link has been sent."
                },
                status=status.HTTP_200_OK,
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # Construct a frontend compatible reset URL
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

    Args:
        generics (GenericAPIView): Provides PUT and POST handlers for updating the user's password.

    Returns:
        A success message on successful password update, or an error message on failure.
    """

    serializer_class = UpdatePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Return the currently authenticated user."""
        return self.request.user

    def _update_password(self, request):
        """Handle the password update process, including validation of the old password and setting the new password."""
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

    Shows a summary of all leave applications with:
    - Overall totals (approved, rejected, pending)
    - Per-user breakdown with details

    Only accessible to HR and Manager roles.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Get leave summary dashboard for HR/Managers."""
        user = request.user

        # Only HR and Managers can access this endpoint
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

        # Get all leaves
        all_leaves = Leave.objects.all()

        # Calculate overall totals
        total_leaves = all_leaves.count()
        total_approved = all_leaves.filter(status="APPROVED").count()
        total_rejected = all_leaves.filter(status="REJECTED").count()
        total_pending = all_leaves.filter(status="PENDING").count()

        # Get all employees
        all_employees = Employee.objects.all()

        # Build per-user breakdown
        user_breakdown = []
        for employee in all_employees:
            emp_leaves = Leave.objects.filter(employee=employee)

            emp_data = {
                "user_id": employee.id,
                "email": employee.email,
                "full_name": f"{employee.first_name} {employee.last_name}".strip(),
                "role": employee.employee_role,
                "department": employee.employee_department,
                "position": employee.employee_position,
                "applications": {
                    "total": emp_leaves.count(),
                    "approved": emp_leaves.filter(status="APPROVED").count(),
                    "rejected": emp_leaves.filter(status="REJECTED").count(),
                    "pending": emp_leaves.filter(status="PENDING").count(),
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
